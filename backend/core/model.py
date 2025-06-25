from typing import List, Optional, Dict, Any, Tuple
from backend.core.node import NodeManager
from backend.core.element import ElementManager
from backend.core.material import MaterialManager
from backend.core.section import SectionManager
from backend.core.load import LoadManager
from backend.db.models import Model, Project
from sqlalchemy.orm import Session


class StructuralModel:
    """Main structural model class that coordinates all components"""
    
    def __init__(self, db_session: Session, model_id: int = None, project_id: int = None):
        self.db = db_session
        
        if model_id:
            self.model = self.db.query(Model).filter(Model.id == model_id).first()
            if not self.model:
                raise ValueError(f"Model {model_id} not found")
        elif project_id:
            # Create new model
            self.model = self._create_new_model(project_id)
        else:
            raise ValueError("Either model_id or project_id must be provided")
        
        # Initialize managers
        self.node_manager = NodeManager(db_session, self.model.id)
        self.element_manager = ElementManager(db_session, self.model.id)
        self.material_manager = MaterialManager(db_session, self.model.id)
        self.section_manager = SectionManager(db_session, self.model.id)
        self.load_manager = LoadManager(db_session, self.model.id)
        
        # Model validation flags
        self._is_valid = None
        self._validation_errors = []
    
    def _create_new_model(self, project_id: int, name: str = "New Model", description: str = "") -> Model:
        """Create a new structural model"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        model = Model(
            name=name,
            description=description,
            project_id=project_id,
            units="metric"
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        return model
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "id": self.model.id,
            "name": self.model.name,
            "description": self.model.description,
            "project_id": self.model.project_id,
            "units": self.model.units,
            "created_at": self.model.created_at,
            "updated_at": self.model.updated_at,
            "stats": self.get_model_statistics()
        }
    
    def get_model_statistics(self) -> Dict[str, int]:
        """Get model statistics"""
        return {
            "nodes": len(self.node_manager.get_all_nodes()),
            "elements": len(self.element_manager.get_all_elements()),
            "materials": len(self.material_manager.get_all_materials()),
            "sections": len(self.section_manager.get_all_sections()),
            "loads": len(self.load_manager.get_all_loads()),
            "load_combinations": len(self.load_manager.get_all_load_combinations())
        }
    
    def validate_model(self) -> Tuple[bool, List[str]]:
        """Validate the structural model"""
        errors = []
        
        # Check if model has nodes
        nodes = self.node_manager.get_all_nodes()
        if not nodes:
            errors.append("Model has no nodes")
        
        # Check if model has elements
        elements = self.element_manager.get_all_elements()
        if not elements:
            errors.append("Model has no elements")
        
        # Check if model has materials
        materials = self.material_manager.get_all_materials()
        if not materials:
            errors.append("Model has no materials")
        
        # Check if model has sections
        sections = self.section_manager.get_all_sections()
        if not sections:
            errors.append("Model has no sections")
        
        # Check element connectivity
        for element in elements:
            if not element.start_node or not element.end_node:
                errors.append(f"Element {element.label} has invalid node connectivity")
            
            if element.start_node_id == element.end_node_id:
                errors.append(f"Element {element.label} has same start and end nodes")
        
        # Check for boundary conditions
        boundary_conditions = []
        for node in nodes:
            bc = self.node_manager.get_boundary_condition(node.id)
            if bc:
                boundary_conditions.append(bc)
        
        if not boundary_conditions:
            errors.append("Model has no boundary conditions (supports)")
        
        # Check for unrestrained structure
        total_restraints = 0
        for bc in boundary_conditions:
            if bc.restrain_x: total_restraints += 1
            if bc.restrain_y: total_restraints += 1
            if bc.restrain_z: total_restraints += 1
            if bc.restrain_rx: total_restraints += 1
            if bc.restrain_ry: total_restraints += 1
            if bc.restrain_rz: total_restraints += 1
        
        if total_restraints < 6:
            errors.append("Structure appears to be unstable (insufficient restraints)")
        
        # Check for loads
        loads = self.load_manager.get_all_loads()
        if not loads:
            errors.append("Model has no loads defined")
        
        # Check material assignments
        for element in elements:
            if not element.material_id:
                errors.append(f"Element {element.label} has no material assigned")
            
            if not element.section_id:
                errors.append(f"Element {element.label} has no section assigned")
        
        # Check for disconnected nodes
        connected_nodes = set()
        for element in elements:
            connected_nodes.add(element.start_node_id)
            connected_nodes.add(element.end_node_id)
        
        all_node_ids = {node.id for node in nodes}
        disconnected_nodes = all_node_ids - connected_nodes
        
        if disconnected_nodes:
            errors.append(f"Found {len(disconnected_nodes)} disconnected nodes")
        
        self._is_valid = len(errors) == 0
        self._validation_errors = errors
        
        return self._is_valid, errors
    
    def get_validation_status(self) -> Tuple[bool, List[str]]:
        """Get cached validation status"""
        if self._is_valid is None:
            return self.validate_model()
        return self._is_valid, self._validation_errors
    
    def create_simple_frame(self, width: float, height: float, bay_width: float = None,
                          num_stories: int = 1, num_bays: int = 1) -> Dict[str, Any]:
        """Create a simple frame structure"""
        
        if bay_width is None:
            bay_width = width / num_bays
        
        created_elements = {
            "nodes": [],
            "columns": [],
            "beams": [],
            "materials": [],
            "sections": []
        }
        
        # Create default materials
        concrete = self.material_manager.create_from_library("M25 Concrete", "concrete", "M25")
        steel = self.material_manager.create_from_library("Fe415 Steel", "steel", "Fe415")
        created_elements["materials"] = [concrete, steel]
        
        # Create default sections
        beam_section = self.section_manager.create_rectangular_section("Beam_300x450", 450, 300)
        column_section = self.section_manager.create_rectangular_section("Column_300x300", 300, 300)
        created_elements["sections"] = [beam_section, column_section]
        
        # Create nodes
        node_counter = 1
        for story in range(num_stories + 1):
            z = story * height
            for bay in range(num_bays + 1):
                x = bay * bay_width
                y = 0.0
                
                label = f"N{node_counter}"
                node = self.node_manager.create_node(label, x, y, z)
                created_elements["nodes"].append(node)
                node_counter += 1
        
        # Create columns
        element_counter = 1
        for story in range(num_stories):
            for bay in range(num_bays + 1):
                start_node_idx = story * (num_bays + 1) + bay
                end_node_idx = (story + 1) * (num_bays + 1) + bay
                
                start_node = created_elements["nodes"][start_node_idx]
                end_node = created_elements["nodes"][end_node_idx]
                
                label = f"C{element_counter}"
                column = self.element_manager.create_column(
                    label, start_node.id, end_node.id, concrete.id, column_section.id
                )
                created_elements["columns"].append(column)
                element_counter += 1
        
        # Create beams
        for story in range(1, num_stories + 1):
            for bay in range(num_bays):
                start_node_idx = story * (num_bays + 1) + bay
                end_node_idx = story * (num_bays + 1) + bay + 1
                
                start_node = created_elements["nodes"][start_node_idx]
                end_node = created_elements["nodes"][end_node_idx]
                
                label = f"B{element_counter}"
                beam = self.element_manager.create_beam(
                    label, start_node.id, end_node.id, concrete.id, beam_section.id
                )
                created_elements["beams"].append(beam)
                element_counter += 1
        
        # Add supports at base nodes
        for bay in range(num_bays + 1):
            base_node = created_elements["nodes"][bay]
            self.node_manager.add_boundary_condition(base_node.id, "fixed")
        
        return created_elements
    
    def create_simple_building(self, length: float, width: float, height: float,
                             num_stories: int = 1, bay_length: float = None, bay_width: float = None) -> Dict[str, Any]:
        """Create a simple building structure"""
        
        if bay_length is None:
            bay_length = length / 3  # Default 3 bays in length
        if bay_width is None:
            bay_width = width / 3   # Default 3 bays in width
        
        num_bays_x = int(length / bay_length)
        num_bays_y = int(width / bay_width)
        
        created_elements = {
            "nodes": [],
            "columns": [],
            "beams_x": [],
            "beams_y": [],
            "materials": [],
            "sections": []
        }
        
        # Create default materials
        concrete = self.material_manager.create_from_library("M25 Concrete", "concrete", "M25")
        created_elements["materials"] = [concrete]
        
        # Create default sections
        beam_section = self.section_manager.create_rectangular_section("Beam_300x450", 450, 300)
        column_section = self.section_manager.create_rectangular_section("Column_300x300", 300, 300)
        created_elements["sections"] = [beam_section, column_section]
        
        # Create nodes
        node_counter = 1
        for story in range(num_stories + 1):
            z = story * height
            for j in range(num_bays_y + 1):
                y = j * bay_width
                for i in range(num_bays_x + 1):
                    x = i * bay_length
                    
                    label = f"N{node_counter}"
                    node = self.node_manager.create_node(label, x, y, z)
                    created_elements["nodes"].append(node)
                    node_counter += 1
        
        # Helper function to get node index
        def get_node_index(story, i, j):
            return story * (num_bays_x + 1) * (num_bays_y + 1) + j * (num_bays_x + 1) + i
        
        # Create columns
        element_counter = 1
        for story in range(num_stories):
            for j in range(num_bays_y + 1):
                for i in range(num_bays_x + 1):
                    start_idx = get_node_index(story, i, j)
                    end_idx = get_node_index(story + 1, i, j)
                    
                    start_node = created_elements["nodes"][start_idx]
                    end_node = created_elements["nodes"][end_idx]
                    
                    label = f"C{element_counter}"
                    column = self.element_manager.create_column(
                        label, start_node.id, end_node.id, concrete.id, column_section.id
                    )
                    created_elements["columns"].append(column)
                    element_counter += 1
        
        # Create beams in X direction
        for story in range(1, num_stories + 1):
            for j in range(num_bays_y + 1):
                for i in range(num_bays_x):
                    start_idx = get_node_index(story, i, j)
                    end_idx = get_node_index(story, i + 1, j)
                    
                    start_node = created_elements["nodes"][start_idx]
                    end_node = created_elements["nodes"][end_idx]
                    
                    label = f"BX{element_counter}"
                    beam = self.element_manager.create_beam(
                        label, start_node.id, end_node.id, concrete.id, beam_section.id
                    )
                    created_elements["beams_x"].append(beam)
                    element_counter += 1
        
        # Create beams in Y direction
        for story in range(1, num_stories + 1):
            for j in range(num_bays_y):
                for i in range(num_bays_x + 1):
                    start_idx = get_node_index(story, i, j)
                    end_idx = get_node_index(story, i, j + 1)
                    
                    start_node = created_elements["nodes"][start_idx]
                    end_node = created_elements["nodes"][end_idx]
                    
                    label = f"BY{element_counter}"
                    beam = self.element_manager.create_beam(
                        label, start_node.id, end_node.id, concrete.id, beam_section.id
                    )
                    created_elements["beams_y"].append(beam)
                    element_counter += 1
        
        # Add supports at base nodes
        for j in range(num_bays_y + 1):
            for i in range(num_bays_x + 1):
                base_idx = get_node_index(0, i, j)
                base_node = created_elements["nodes"][base_idx]
                self.node_manager.add_boundary_condition(base_node.id, "fixed")
        
        return created_elements
    
    def apply_standard_loads(self, dead_load: float = 25.0, live_load: float = 3.0,
                           floor_finish: float = 1.0) -> List:
        """Apply standard building loads"""
        
        loads = []
        
        # Apply dead loads to all beams
        beams = self.element_manager.get_elements_by_type("beam")
        for beam in beams:
            # Self weight is automatically calculated
            # Additional dead load for finishes, etc.
            dl = self.load_manager.create_distributed_load(
                f"DL_{beam.label}", "DL", beam.id, force_z=-dead_load
            )
            loads.append(dl)
            
            # Floor finish load
            ff = self.load_manager.create_distributed_load(
                f"FF_{beam.label}", "DL", beam.id, force_z=-floor_finish
            )
            loads.append(ff)
        
        # Apply live loads to beams
        for beam in beams:
            ll = self.load_manager.create_distributed_load(
                f"LL_{beam.label}", "LL", beam.id, force_z=-live_load
            )
            loads.append(ll)
        
        return loads
    
    def export_model_data(self) -> Dict[str, Any]:
        """Export complete model data"""
        
        # Get all model components
        nodes = self.node_manager.get_all_nodes()
        elements = self.element_manager.get_all_elements()
        materials = self.material_manager.get_all_materials()
        sections = self.section_manager.get_all_sections()
        loads = self.load_manager.get_all_loads()
        load_combinations = self.load_manager.get_all_load_combinations()
        
        # Get boundary conditions
        boundary_conditions = []
        for node in nodes:
            bc = self.node_manager.get_boundary_condition(node.id)
            if bc:
                boundary_conditions.append({
                    "node_id": bc.node_id,
                    "support_type": bc.support_type,
                    "restrain_x": bc.restrain_x,
                    "restrain_y": bc.restrain_y,
                    "restrain_z": bc.restrain_z,
                    "restrain_rx": bc.restrain_rx,
                    "restrain_ry": bc.restrain_ry,
                    "restrain_rz": bc.restrain_rz
                })
        
        return {
            "model_info": self.get_model_info(),
            "nodes": [{"id": n.id, "label": n.label, "x": n.x, "y": n.y, "z": n.z} for n in nodes],
            "elements": [{
                "id": e.id, "label": e.label, "type": e.element_type,
                "start_node_id": e.start_node_id, "end_node_id": e.end_node_id,
                "material_id": e.material_id, "section_id": e.section_id,
                "orientation_angle": e.orientation_angle, "releases": e.releases
            } for e in elements],
            "materials": [{
                "id": m.id, "name": m.name, "type": m.material_type,
                "elastic_modulus": m.elastic_modulus, "poisson_ratio": m.poisson_ratio,
                "density": m.density, "yield_strength": m.yield_strength,
                "ultimate_strength": m.ultimate_strength, "compressive_strength": m.compressive_strength,
                "design_code": m.design_code, "grade": m.grade
            } for m in materials],
            "sections": [{
                "id": s.id, "name": s.name, "type": s.section_type,
                "area": s.area, "iy": s.moment_of_inertia_y, "iz": s.moment_of_inertia_z,
                "j": s.torsional_constant, "zy": s.section_modulus_y, "zz": s.section_modulus_z,
                "dimensions": s.dimensions
            } for s in sections],
            "loads": [{
                "id": l.id, "name": l.name, "type": l.load_type, "case": l.load_case,
                "element_id": l.element_id, "node_id": l.node_id,
                "fx": l.force_x, "fy": l.force_y, "fz": l.force_z,
                "mx": l.moment_x, "my": l.moment_y, "mz": l.moment_z,
                "start_distance": l.start_distance, "end_distance": l.end_distance
            } for l in loads],
            "load_combinations": [{
                "id": lc.id, "name": lc.name, "type": lc.combination_type,
                "factors": lc.factors
            } for lc in load_combinations],
            "boundary_conditions": boundary_conditions
        }
    
    def clear_model(self):
        """Clear all model data"""
        
        # Delete all loads
        for load in self.load_manager.get_all_loads():
            self.load_manager.delete_load(load.id)
        
        # Delete all load combinations
        for combo in self.load_manager.get_all_load_combinations():
            self.load_manager.delete_load_combination(combo.id)
        
        # Delete all elements
        for element in self.element_manager.get_all_elements():
            self.element_manager.delete_element(element.id)
        
        # Delete all boundary conditions
        for node in self.node_manager.get_all_nodes():
            self.node_manager.remove_boundary_condition(node.id)
        
        # Delete all nodes
        for node in self.node_manager.get_all_nodes():
            self.node_manager.delete_node(node.id)
        
        # Delete all sections
        for section in self.section_manager.get_all_sections():
            self.section_manager.delete_section(section.id)
        
        # Delete all materials
        for material in self.material_manager.get_all_materials():
            self.material_manager.delete_material(material.id)
        
        # Reset validation status
        self._is_valid = None
        self._validation_errors = []
