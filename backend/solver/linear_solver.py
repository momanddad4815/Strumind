import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import spsolve
from scipy.linalg import solve
import logging


class LinearSolver:
    """Linear static analysis solver"""
    
    def __init__(self, stiffness_matrix: csc_matrix, load_vector: np.ndarray):
        self.K = stiffness_matrix
        self.F = load_vector
        self.displacements = None
        self.reactions = None
        self.solved = False
        
        # Solver parameters
        self.tolerance = 1e-12
        self.max_iterations = 1000
        
        # Results storage
        self.results = {}
        
    def solve(self) -> Dict[str, np.ndarray]:
        """Solve the linear system K*u = F"""
        
        try:
            # Check matrix conditioning
            if self._check_matrix_conditioning():
                # Solve using sparse solver
                self.displacements = spsolve(self.K, self.F)
                
                # Calculate reactions
                self.reactions = self.K @ self.displacements - self.F
                
                self.solved = True
                
                # Store results
                self.results = {
                    'displacements': self.displacements,
                    'reactions': self.reactions,
                    'status': 'converged',
                    'error': 0.0
                }
                
                logging.info("Linear analysis completed successfully")
                
            else:
                self.results = {
                    'displacements': np.zeros_like(self.F),
                    'reactions': np.zeros_like(self.F),
                    'status': 'failed',
                    'error': 'Matrix is singular or poorly conditioned'
                }
                
                logging.error("Matrix is singular or poorly conditioned")
                
        except Exception as e:
            self.results = {
                'displacements': np.zeros_like(self.F),
                'reactions': np.zeros_like(self.F),
                'status': 'failed',
                'error': str(e)
            }
            
            logging.error(f"Linear analysis failed: {str(e)}")
        
        return self.results
    
    def _check_matrix_conditioning(self) -> bool:
        """Check if stiffness matrix is well-conditioned"""
        
        try:
            # Check for zero diagonal terms
            diagonal = self.K.diagonal()
            if np.any(np.abs(diagonal) < self.tolerance):
                logging.warning("Zero diagonal terms found in stiffness matrix")
                return False
            
            # For small matrices, check condition number
            if self.K.shape[0] < 1000:
                K_dense = self.K.toarray()
                cond_num = np.linalg.cond(K_dense)
                if cond_num > 1e12:
                    logging.warning(f"High condition number: {cond_num}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking matrix conditioning: {str(e)}")
            return False
    
    def get_nodal_displacements(self, node_indices: List[int], dof_per_node: int = 6) -> Dict[int, np.ndarray]:
        """Get displacements for specific nodes"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        nodal_displacements = {}
        
        for node_index in node_indices:
            start_dof = node_index * dof_per_node
            end_dof = start_dof + dof_per_node
            
            nodal_displacements[node_index] = {
                'ux': self.displacements[start_dof + 0],
                'uy': self.displacements[start_dof + 1],
                'uz': self.displacements[start_dof + 2],
                'rx': self.displacements[start_dof + 3],
                'ry': self.displacements[start_dof + 4],
                'rz': self.displacements[start_dof + 5]
            }
        
        return nodal_displacements
    
    def get_reaction_forces(self, restrained_node_indices: List[int], dof_per_node: int = 6) -> Dict[int, np.ndarray]:
        """Get reaction forces at restrained nodes"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        reaction_forces = {}
        
        for node_index in restrained_node_indices:
            start_dof = node_index * dof_per_node
            end_dof = start_dof + dof_per_node
            
            reaction_forces[node_index] = {
                'fx': self.reactions[start_dof + 0],
                'fy': self.reactions[start_dof + 1],
                'fz': self.reactions[start_dof + 2],
                'mx': self.reactions[start_dof + 3],
                'my': self.reactions[start_dof + 4],
                'mz': self.reactions[start_dof + 5]
            }
        
        return reaction_forces
    
    def calculate_element_forces(self, elements: List, nodes: Dict, materials: Dict, 
                               sections: Dict, node_to_index: Dict) -> Dict[int, Dict]:
        """Calculate element internal forces"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        element_forces = {}
        
        for element in elements:
            # Get element displacement vector
            start_node_index = node_to_index[element.start_node_id]
            end_node_index = node_to_index[element.end_node_id]
            
            element_displacements = np.zeros(12)
            
            # Start node displacements
            start_dof = start_node_index * 6
            element_displacements[0:6] = self.displacements[start_dof:start_dof+6]
            
            # End node displacements
            end_dof = end_node_index * 6
            element_displacements[6:12] = self.displacements[end_dof:end_dof+6]
            
            # Calculate element forces
            forces = self._calculate_element_internal_forces(
                element, element_displacements, nodes, materials, sections
            )
            
            element_forces[element.id] = forces
        
        return element_forces
    
    def _calculate_element_internal_forces(self, element, element_displacements: np.ndarray,
                                         nodes: Dict, materials: Dict, sections: Dict) -> Dict:
        """Calculate internal forces for a single element"""
        
        from backend.solver.matrix_assembler import MatrixAssembler
        from backend.core.geometry import Point3D, GeometryUtils
        
        # Get element properties
        material = materials[element.material_id]
        section = sections[element.section_id]
        
        start_node = nodes[element.start_node_id]
        end_node = nodes[element.end_node_id]
        
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
        
        # Local stiffness matrix
        assembler = MatrixAssembler([], [], {}, {}, [])
        K_local = assembler._frame_element_stiffness_3d(E, G, A, Iy, Iz, J, length)
        
        # Transformation matrix
        T = assembler._get_transformation_matrix_3d(start_point, end_point, element.orientation_angle)
        
        # Transform displacements to local coordinates
        local_displacements = T @ element_displacements
        
        # Calculate local forces
        local_forces = K_local @ local_displacements
        
        # Extract forces at start and end nodes
        start_forces = {
            'N': local_forces[0],      # Axial force
            'Vy': local_forces[1],     # Shear force in y
            'Vz': local_forces[2],     # Shear force in z
            'T': local_forces[3],      # Torsion
            'My': local_forces[4],     # Moment about y
            'Mz': local_forces[5]      # Moment about z
        }
        
        end_forces = {
            'N': local_forces[6],      # Axial force
            'Vy': local_forces[7],     # Shear force in y
            'Vz': local_forces[8],     # Shear force in z
            'T': local_forces[9],      # Torsion
            'My': local_forces[10],    # Moment about y
            'Mz': local_forces[11]     # Moment about z
        }
        
        # Calculate maximum moments and shears along element length
        max_moment_y = max(abs(start_forces['My']), abs(end_forces['My']))
        max_moment_z = max(abs(start_forces['Mz']), abs(end_forces['Mz']))
        max_shear_y = max(abs(start_forces['Vy']), abs(end_forces['Vy']))
        max_shear_z = max(abs(start_forces['Vz']), abs(end_forces['Vz']))
        
        return {
            'start_node': start_forces,
            'end_node': end_forces,
            'max_axial': abs(start_forces['N']),
            'max_moment_y': max_moment_y,
            'max_moment_z': max_moment_z,
            'max_shear_y': max_shear_y,
            'max_shear_z': max_shear_z,
            'max_torsion': max(abs(start_forces['T']), abs(end_forces['T']))
        }
    
    def get_maximum_displacements(self, dof_per_node: int = 6) -> Dict[str, float]:
        """Get maximum displacements in each direction"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        num_nodes = len(self.displacements) // dof_per_node
        
        # Extract displacement components
        ux = self.displacements[0::dof_per_node]
        uy = self.displacements[1::dof_per_node]
        uz = self.displacements[2::dof_per_node]
        rx = self.displacements[3::dof_per_node]
        ry = self.displacements[4::dof_per_node]
        rz = self.displacements[5::dof_per_node]
        
        return {
            'max_ux': np.max(np.abs(ux)),
            'max_uy': np.max(np.abs(uy)),
            'max_uz': np.max(np.abs(uz)),
            'max_rx': np.max(np.abs(rx)),
            'max_ry': np.max(np.abs(ry)),
            'max_rz': np.max(np.abs(rz)),
            'max_total_translation': np.max(np.sqrt(ux**2 + uy**2 + uz**2)),
            'max_total_rotation': np.max(np.sqrt(rx**2 + ry**2 + rz**2))
        }
    
    def get_total_reaction_forces(self, restrained_indices: List[int], dof_per_node: int = 6) -> Dict[str, float]:
        """Get total reaction forces and moments"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        total_fx = 0.0
        total_fy = 0.0
        total_fz = 0.0
        total_mx = 0.0
        total_my = 0.0
        total_mz = 0.0
        
        for node_index in restrained_indices:
            start_dof = node_index * dof_per_node
            
            total_fx += self.reactions[start_dof + 0]
            total_fy += self.reactions[start_dof + 1]
            total_fz += self.reactions[start_dof + 2]
            total_mx += self.reactions[start_dof + 3]
            total_my += self.reactions[start_dof + 4]
            total_mz += self.reactions[start_dof + 5]
        
        return {
            'total_fx': total_fx,
            'total_fy': total_fy,
            'total_fz': total_fz,
            'total_mx': total_mx,
            'total_my': total_my,
            'total_mz': total_mz
        }
    
    def check_equilibrium(self, applied_loads: np.ndarray, tolerance: float = 1e-6) -> Dict[str, bool]:
        """Check global equilibrium"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        # Calculate residual forces
        residual = self.K @ self.displacements - applied_loads
        
        # Check equilibrium in each direction
        max_residual = np.max(np.abs(residual))
        
        equilibrium_check = {
            'equilibrium_satisfied': max_residual < tolerance,
            'max_residual_force': max_residual,
            'tolerance': tolerance
        }
        
        return equilibrium_check
    
    def export_results(self) -> Dict:
        """Export all analysis results"""
        
        if not self.solved:
            raise ValueError("Analysis not solved yet")
        
        return {
            'analysis_type': 'linear_static',
            'status': self.results['status'],
            'displacements': self.displacements.tolist(),
            'reactions': self.reactions.tolist(),
            'max_displacements': self.get_maximum_displacements(),
            'solver_info': {
                'matrix_size': self.K.shape[0],
                'non_zeros': self.K.nnz,
                'tolerance': self.tolerance
            }
        }
