import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.sparse import csc_matrix, lil_matrix
from backend.core.geometry import Point3D, GeometryUtils
from backend.db.models import Node, Element, Material, Section, BoundaryCondition


class MatrixAssembler:
    """Assembles global stiffness matrix and load vectors"""
    
    def __init__(self, nodes: List[Node], elements: List[Element], 
                 materials: Dict[int, Material], sections: Dict[int, Section],
                 boundary_conditions: List[BoundaryCondition]):
        self.nodes = {node.id: node for node in nodes}
        self.elements = {element.id: element for element in elements}
        self.materials = materials
        self.sections = sections
        self.boundary_conditions = {bc.node_id: bc for bc in boundary_conditions}
        
        # Create node numbering
        self.node_ids = sorted(self.nodes.keys())
        self.node_to_index = {node_id: i for i, node_id in enumerate(self.node_ids)}
        
        # Degrees of freedom (6 DOF per node: 3 translations + 3 rotations)
        self.dof_per_node = 6
        self.total_dof = len(self.nodes) * self.dof_per_node
        
        # Initialize global matrices
        self.global_stiffness = None
        self.global_mass = None
        self.global_load = None
        
    def assemble_global_stiffness_matrix(self) -> csc_matrix:
        """Assemble global stiffness matrix"""
        
        # Use sparse matrix for efficiency
        K_global = lil_matrix((self.total_dof, self.total_dof))
        
        for element in self.elements.values():
            # Get element stiffness matrix
            K_element = self._get_element_stiffness_matrix(element)
            
            # Get element DOF indices
            element_dofs = self._get_element_dof_indices(element)
            
            # Assemble into global matrix
            for i, global_i in enumerate(element_dofs):
                for j, global_j in enumerate(element_dofs):
                    K_global[global_i, global_j] += K_element[i, j]
        
        # Apply boundary conditions
        K_global = self._apply_boundary_conditions(K_global)
        
        self.global_stiffness = K_global.tocsc()
        return self.global_stiffness
    
    def assemble_global_mass_matrix(self) -> csc_matrix:
        """Assemble global mass matrix"""
        
        M_global = lil_matrix((self.total_dof, self.total_dof))
        
        for element in self.elements.values():
            # Get element mass matrix
            M_element = self._get_element_mass_matrix(element)
            
            # Get element DOF indices
            element_dofs = self._get_element_dof_indices(element)
            
            # Assemble into global matrix
            for i, global_i in enumerate(element_dofs):
                for j, global_j in enumerate(element_dofs):
                    M_global[global_i, global_j] += M_element[i, j]
        
        self.global_mass = M_global.tocsc()
        return self.global_mass
    
    def assemble_load_vector(self, loads: List, load_combination_factors: Dict[str, float] = None) -> np.ndarray:
        """Assemble global load vector"""
        
        F_global = np.zeros(self.total_dof)
        
        for load in loads:
            if load_combination_factors:
                factor = load_combination_factors.get(load.load_case, 0.0)
            else:
                factor = 1.0
            
            if load.node_id:
                # Point load
                node_index = self.node_to_index[load.node_id]
                base_dof = node_index * self.dof_per_node
                
                F_global[base_dof + 0] += factor * load.force_x
                F_global[base_dof + 1] += factor * load.force_y
                F_global[base_dof + 2] += factor * load.force_z
                F_global[base_dof + 3] += factor * load.moment_x
                F_global[base_dof + 4] += factor * load.moment_y
                F_global[base_dof + 5] += factor * load.moment_z
            
            elif load.element_id:
                # Distributed load - convert to equivalent nodal loads
                element = self.elements[load.element_id]
                equivalent_loads = self._convert_distributed_to_nodal(load, element)
                
                for node_load in equivalent_loads:
                    node_index = self.node_to_index[node_load['node_id']]
                    base_dof = node_index * self.dof_per_node
                    
                    F_global[base_dof + 0] += factor * node_load['fx']
                    F_global[base_dof + 1] += factor * node_load['fy']
                    F_global[base_dof + 2] += factor * node_load['fz']
                    F_global[base_dof + 3] += factor * node_load['mx']
                    F_global[base_dof + 4] += factor * node_load['my']
                    F_global[base_dof + 5] += factor * node_load['mz']
        
        self.global_load = F_global
        return F_global
    
    def _get_element_stiffness_matrix(self, element: Element) -> np.ndarray:
        """Get element stiffness matrix in global coordinates"""
        
        # Get material and section properties
        material = self.materials[element.material_id]
        section = self.sections[element.section_id]
        
        # Get element geometry
        start_node = self.nodes[element.start_node_id]
        end_node = self.nodes[element.end_node_id]
        
        start_point = Point3D(start_node.x, start_node.y, start_node.z)
        end_point = Point3D(end_node.x, end_node.y, end_node.z)
        
        length = GeometryUtils.calculate_element_length(start_point, end_point)
        
        # Material properties
        E = material.elastic_modulus * 1000  # Convert to N/m²
        G = E / (2 * (1 + material.poisson_ratio))
        
        # Section properties (convert to m²)
        A = section.area / 1e6  # mm² to m²
        Iy = section.moment_of_inertia_y / 1e12  # mm⁴ to m⁴
        Iz = section.moment_of_inertia_z / 1e12  # mm⁴ to m⁴
        J = section.torsional_constant / 1e12  # mm⁴ to m⁴
        
        # Local stiffness matrix for 3D frame element
        K_local = self._frame_element_stiffness_3d(E, G, A, Iy, Iz, J, length)
        
        # Transformation matrix
        T = self._get_transformation_matrix_3d(start_point, end_point, element.orientation_angle)
        
        # Transform to global coordinates
        K_global = T.T @ K_local @ T
        
        # Apply releases if any
        if element.releases:
            K_global = self._apply_element_releases(K_global, element.releases)
        
        return K_global
    
    def _get_element_mass_matrix(self, element: Element) -> np.ndarray:
        """Get element mass matrix in global coordinates"""
        
        # Get material and section properties
        material = self.materials[element.material_id]
        section = self.sections[element.section_id]
        
        # Get element geometry
        start_node = self.nodes[element.start_node_id]
        end_node = self.nodes[element.end_node_id]
        
        start_point = Point3D(start_node.x, start_node.y, start_node.z)
        end_point = Point3D(end_node.x, end_node.y, end_node.z)
        
        length = GeometryUtils.calculate_element_length(start_point, end_point)
        
        # Mass properties
        rho = material.density  # kg/m³
        A = section.area / 1e6  # mm² to m²
        
        # Local mass matrix for 3D frame element (consistent mass matrix)
        M_local = self._frame_element_mass_3d(rho, A, length)
        
        # Transformation matrix
        T = self._get_transformation_matrix_3d(start_point, end_point, element.orientation_angle)
        
        # Transform to global coordinates
        M_global = T.T @ M_local @ T
        
        return M_global
    
    def _frame_element_stiffness_3d(self, E: float, G: float, A: float, 
                                   Iy: float, Iz: float, J: float, L: float) -> np.ndarray:
        """3D frame element stiffness matrix in local coordinates"""
        
        # Initialize 12x12 stiffness matrix
        K = np.zeros((12, 12))
        
        # Axial stiffness
        EA_L = E * A / L
        K[0, 0] = K[6, 6] = EA_L
        K[0, 6] = K[6, 0] = -EA_L
        
        # Shear in local y direction (bending about z-axis)
        EIz_L = E * Iz / L
        EIz_L3 = E * Iz / (L**3)
        
        K[1, 1] = K[7, 7] = 12 * EIz_L3
        K[1, 5] = K[5, 1] = K[7, 11] = K[11, 7] = 6 * EIz_L / L
        K[1, 7] = K[7, 1] = -12 * EIz_L3
        K[1, 11] = K[11, 1] = K[5, 7] = K[7, 5] = -6 * EIz_L / L
        K[5, 5] = K[11, 11] = 4 * EIz_L
        K[5, 11] = K[11, 5] = 2 * EIz_L
        
        # Shear in local z direction (bending about y-axis)
        EIy_L = E * Iy / L
        EIy_L3 = E * Iy / (L**3)
        
        K[2, 2] = K[8, 8] = 12 * EIy_L3
        K[2, 4] = K[4, 2] = K[8, 10] = K[10, 8] = -6 * EIy_L / L
        K[2, 8] = K[8, 2] = -12 * EIy_L3
        K[2, 10] = K[10, 2] = K[4, 8] = K[8, 4] = 6 * EIy_L / L
        K[4, 4] = K[10, 10] = 4 * EIy_L
        K[4, 10] = K[10, 4] = 2 * EIy_L
        
        # Torsion
        GJ_L = G * J / L
        K[3, 3] = K[9, 9] = GJ_L
        K[3, 9] = K[9, 3] = -GJ_L
        
        return K
    
    def _frame_element_mass_3d(self, rho: float, A: float, L: float) -> np.ndarray:
        """3D frame element consistent mass matrix in local coordinates"""
        
        # Mass per unit length
        m = rho * A
        
        # Initialize 12x12 mass matrix
        M = np.zeros((12, 12))
        
        # Translational mass terms
        M[0, 0] = M[6, 6] = m * L / 3
        M[0, 6] = M[6, 0] = m * L / 6
        
        M[1, 1] = M[7, 7] = 13 * m * L / 35
        M[1, 5] = M[5, 1] = M[7, 11] = M[11, 7] = 11 * m * L**2 / 210
        M[1, 7] = M[7, 1] = 9 * m * L / 70
        M[1, 11] = M[11, 1] = -13 * m * L**2 / 420
        M[5, 7] = M[7, 5] = -13 * m * L**2 / 420
        
        M[2, 2] = M[8, 8] = 13 * m * L / 35
        M[2, 4] = M[4, 2] = M[8, 10] = M[10, 8] = -11 * m * L**2 / 210
        M[2, 8] = M[8, 2] = 9 * m * L / 70
        M[2, 10] = M[10, 2] = 13 * m * L**2 / 420
        M[4, 8] = M[8, 4] = 13 * m * L**2 / 420
        
        # Rotational mass terms (approximate)
        M[3, 3] = M[9, 9] = m * L / 3  # Polar moment approximation
        M[3, 9] = M[9, 3] = m * L / 6
        
        M[4, 4] = M[10, 10] = m * L**3 / 105
        M[4, 10] = M[10, 4] = -m * L**3 / 140
        
        M[5, 5] = M[11, 11] = m * L**3 / 105
        M[5, 11] = M[11, 5] = -m * L**3 / 140
        
        return M
    
    def _get_transformation_matrix_3d(self, start_point: Point3D, end_point: Point3D, 
                                    orientation_angle: float = 0.0) -> np.ndarray:
        """Get 3D transformation matrix from local to global coordinates"""
        
        # Get local coordinate system
        local_coords = GeometryUtils.calculate_local_coordinate_system(
            start_point, end_point, orientation_angle
        )
        
        # Create full transformation matrix (12x12)
        T = np.zeros((12, 12))
        
        # Fill in 3x3 rotation matrices for each DOF set
        for i in range(4):
            start_row = i * 3
            end_row = start_row + 3
            T[start_row:end_row, start_row:end_row] = local_coords
        
        return T
    
    def _get_element_dof_indices(self, element: Element) -> List[int]:
        """Get global DOF indices for element"""
        
        start_node_index = self.node_to_index[element.start_node_id]
        end_node_index = self.node_to_index[element.end_node_id]
        
        start_dofs = [start_node_index * self.dof_per_node + i for i in range(self.dof_per_node)]
        end_dofs = [end_node_index * self.dof_per_node + i for i in range(self.dof_per_node)]
        
        return start_dofs + end_dofs
    
    def _apply_boundary_conditions(self, K_global: lil_matrix) -> lil_matrix:
        """Apply boundary conditions to global stiffness matrix"""
        
        for node_id, bc in self.boundary_conditions.items():
            node_index = self.node_to_index[node_id]
            base_dof = node_index * self.dof_per_node
            
            # Apply restraints by modifying stiffness matrix
            restraints = [bc.restrain_x, bc.restrain_y, bc.restrain_z,
                         bc.restrain_rx, bc.restrain_ry, bc.restrain_rz]
            
            for i, restrained in enumerate(restraints):
                if restrained:
                    dof = base_dof + i
                    # Set diagonal term to large value and off-diagonal to zero
                    K_global[dof, :] = 0
                    K_global[:, dof] = 0
                    K_global[dof, dof] = 1e12  # Large stiffness for restrained DOF
            
            # Add spring stiffnesses if specified
            if bc.spring_kx and not bc.restrain_x:
                K_global[base_dof + 0, base_dof + 0] += bc.spring_kx
            if bc.spring_ky and not bc.restrain_y:
                K_global[base_dof + 1, base_dof + 1] += bc.spring_ky
            if bc.spring_kz and not bc.restrain_z:
                K_global[base_dof + 2, base_dof + 2] += bc.spring_kz
            if bc.spring_krx and not bc.restrain_rx:
                K_global[base_dof + 3, base_dof + 3] += bc.spring_krx
            if bc.spring_kry and not bc.restrain_ry:
                K_global[base_dof + 4, base_dof + 4] += bc.spring_kry
            if bc.spring_krz and not bc.restrain_rz:
                K_global[base_dof + 5, base_dof + 5] += bc.spring_krz
        
        return K_global
    
    def _apply_element_releases(self, K_element: np.ndarray, releases: Dict) -> np.ndarray:
        """Apply element releases to stiffness matrix"""
        
        K_modified = K_element.copy()
        
        # Start node releases
        if 'start' in releases:
            start_releases = releases['start']
            for release_type, is_released in start_releases.items():
                if is_released:
                    if release_type == 'moment_y':
                        # Release moment about y-axis (DOF 4)
                        K_modified[4, :] = 0
                        K_modified[:, 4] = 0
                    elif release_type == 'moment_z':
                        # Release moment about z-axis (DOF 5)
                        K_modified[5, :] = 0
                        K_modified[:, 5] = 0
                    elif release_type == 'moment_x':
                        # Release torsion (DOF 3)
                        K_modified[3, :] = 0
                        K_modified[:, 3] = 0
        
        # End node releases
        if 'end' in releases:
            end_releases = releases['end']
            for release_type, is_released in end_releases.items():
                if is_released:
                    if release_type == 'moment_y':
                        # Release moment about y-axis (DOF 10)
                        K_modified[10, :] = 0
                        K_modified[:, 10] = 0
                    elif release_type == 'moment_z':
                        # Release moment about z-axis (DOF 11)
                        K_modified[11, :] = 0
                        K_modified[:, 11] = 0
                    elif release_type == 'moment_x':
                        # Release torsion (DOF 9)
                        K_modified[9, :] = 0
                        K_modified[:, 9] = 0
        
        return K_modified
    
    def _convert_distributed_to_nodal(self, load, element: Element) -> List[Dict]:
        """Convert distributed load to equivalent nodal loads"""
        
        # Get element geometry
        start_node = self.nodes[element.start_node_id]
        end_node = self.nodes[element.end_node_id]
        
        start_point = Point3D(start_node.x, start_node.y, start_node.z)
        end_point = Point3D(end_node.x, end_node.y, end_node.z)
        
        length = GeometryUtils.calculate_element_length(start_point, end_point)
        
        # Load parameters
        w_x = load.force_x  # Force per unit length
        w_y = load.force_y
        w_z = load.force_z
        
        start_dist = load.start_distance if load.start_distance else 0.0
        end_dist = load.end_distance if load.end_distance else length
        load_length = end_dist - start_dist
        
        # For uniform distributed load, use standard conversion
        # Total load
        P_x = w_x * load_length
        P_y = w_y * load_length
        P_z = w_z * load_length
        
        # For uniform load, each node gets half the total load
        # Plus moments for transverse loads
        equivalent_loads = []
        
        # Start node
        equivalent_loads.append({
            'node_id': element.start_node_id,
            'fx': P_x / 2,
            'fy': P_y / 2,
            'fz': P_z / 2,
            'mx': 0.0,
            'my': w_z * load_length**2 / 12,  # Fixed-end moment for UDL
            'mz': -w_y * load_length**2 / 12
        })
        
        # End node
        equivalent_loads.append({
            'node_id': element.end_node_id,
            'fx': P_x / 2,
            'fy': P_y / 2,
            'fz': P_z / 2,
            'mx': 0.0,
            'my': -w_z * load_length**2 / 12,  # Fixed-end moment for UDL
            'mz': w_y * load_length**2 / 12
        })
        
        return equivalent_loads
    
    def get_free_dof_indices(self) -> List[int]:
        """Get indices of free (unrestrained) DOFs"""
        
        free_dofs = []
        
        for i, node_id in enumerate(self.node_ids):
            base_dof = i * self.dof_per_node
            
            if node_id in self.boundary_conditions:
                bc = self.boundary_conditions[node_id]
                restraints = [bc.restrain_x, bc.restrain_y, bc.restrain_z,
                             bc.restrain_rx, bc.restrain_ry, bc.restrain_rz]
                
                for j, restrained in enumerate(restraints):
                    if not restrained:
                        free_dofs.append(base_dof + j)
            else:
                # All DOFs are free
                for j in range(self.dof_per_node):
                    free_dofs.append(base_dof + j)
        
        return free_dofs
    
    def get_node_coordinates_matrix(self) -> np.ndarray:
        """Get matrix of node coordinates"""
        
        coordinates = np.zeros((len(self.nodes), 3))
        
        for i, node_id in enumerate(self.node_ids):
            node = self.nodes[node_id]
            coordinates[i] = [node.x, node.y, node.z]
        
        return coordinates
