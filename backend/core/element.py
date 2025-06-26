from typing import List, Optional, Dict, Any
import numpy as np
from core.geometry import Point3D, GeometryUtils
from db.models import Element, ElementType, Node, Material, Section
from sqlalchemy.orm import Session


class ElementManager:
    def __init__(self, db_session: Session, model_id: int):
        self.db = db_session
        self.model_id = model_id
        self._elements_cache = {}
        self._load_elements()
    
    def _load_elements(self):
        elements = self.db.query(Element).filter(Element.model_id == self.model_id).all()
        for element in elements:
            self._elements_cache[element.id] = element
    
    def create_element(self, label: str, element_type: ElementType,
                      start_node_id: int, end_node_id: int,
                      material_id: int, section_id: int,
                      orientation_angle: float = 0.0,
                      releases: Dict[str, Any] = None) -> Element:
        
        # Validate nodes exist
        start_node = self.db.query(Node).filter(Node.id == start_node_id).first()
        end_node = self.db.query(Node).filter(Node.id == end_node_id).first()
        
        if not start_node or not end_node:
            raise ValueError("Start or end node not found")
        
        if start_node_id == end_node_id:
            raise ValueError("Start and end nodes cannot be the same")
        
        # Validate material and section exist
        material = self.db.query(Material).filter(Material.id == material_id).first()
        section = self.db.query(Section).filter(Section.id == section_id).first()
        
        if not material or not section:
            raise ValueError("Material or section not found")
        
        # Create element
        element = Element(
            model_id=self.model_id,
            label=label,
            element_type=element_type,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            material_id=material_id,
            section_id=section_id,
            orientation_angle=orientation_angle,
            releases=releases or {}
        )
        
        self.db.add(element)
        self.db.commit()
        self.db.refresh(element)
        
        self._elements_cache[element.id] = element
        return element
    
    def get_element(self, element_id: int) -> Optional[Element]:
        return self._elements_cache.get(element_id)
    
    def get_element_by_label(self, label: str) -> Optional[Element]:
        for element in self._elements_cache.values():
            if element.label == label:
                return element
        return None
    
    def get_all_elements(self) -> List[Element]:
        return list(self._elements_cache.values())
    
    def get_elements_by_type(self, element_type: ElementType) -> List[Element]:
        return [elem for elem in self._elements_cache.values() if elem.element_type == element_type]
    
    def get_elements_connected_to_node(self, node_id: int) -> List[Element]:
        return [elem for elem in self._elements_cache.values() 
                if elem.start_node_id == node_id or elem.end_node_id == node_id]
    
    def update_element_material(self, element_id: int, material_id: int) -> bool:
        element = self.get_element(element_id)
        if not element:
            return False
        
        # Validate material exists
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return False
        
        element.material_id = material_id
        self.db.commit()
        return True
    
    def update_element_section(self, element_id: int, section_id: int) -> bool:
        element = self.get_element(element_id)
        if not element:
            return False
        
        # Validate section exists
        section = self.db.query(Section).filter(Section.id == section_id).first()
        if not section:
            return False
        
        element.section_id = section_id
        self.db.commit()
        return True
    
    def update_element_releases(self, element_id: int, releases: Dict[str, Any]) -> bool:
        element = self.get_element(element_id)
        if not element:
            return False
        
        element.releases = releases
        self.db.commit()
        return True
    
    def delete_element(self, element_id: int) -> bool:
        element = self.get_element(element_id)
        if not element:
            return False
        
        self.db.delete(element)
        self.db.commit()
        
        if element_id in self._elements_cache:
            del self._elements_cache[element_id]
        
        return True
    
    def calculate_element_length(self, element_id: int) -> Optional[float]:
        element = self.get_element(element_id)
        if not element:
            return None
        
        start_node = element.start_node
        end_node = element.end_node
        
        start_point = Point3D(start_node.x, start_node.y, start_node.z)
        end_point = Point3D(end_node.x, end_node.y, end_node.z)
        
        return GeometryUtils.calculate_element_length(start_point, end_point)
    
    def calculate_element_direction_cosines(self, element_id: int) -> Optional[tuple]:
        element = self.get_element(element_id)
        if not element:
            return None
        
        start_node = element.start_node
        end_node = element.end_node
        
        start_point = Point3D(start_node.x, start_node.y, start_node.z)
        end_point = Point3D(end_node.x, end_node.y, end_node.z)
        
        return GeometryUtils.calculate_element_direction_cosines(start_point, end_point)
    
    def get_element_transformation_matrix(self, element_id: int) -> Optional[np.ndarray]:
        element = self.get_element(element_id)
        if not element:
            return None
        
        start_node = element.start_node
        end_node = element.end_node
        
        start_point = Point3D(start_node.x, start_node.y, start_node.z)
        end_point = Point3D(end_node.x, end_node.y, end_node.z)
        
        return GeometryUtils.calculate_local_coordinate_system(
            start_point, end_point, element.orientation_angle
        )
    
    def create_beam(self, label: str, start_node_id: int, end_node_id: int,
                   material_id: int, section_id: int, orientation_angle: float = 0.0) -> Element:
        return self.create_element(
            label, ElementType.BEAM, start_node_id, end_node_id,
            material_id, section_id, orientation_angle
        )
    
    def create_column(self, label: str, start_node_id: int, end_node_id: int,
                     material_id: int, section_id: int, orientation_angle: float = 0.0) -> Element:
        return self.create_element(
            label, ElementType.COLUMN, start_node_id, end_node_id,
            material_id, section_id, orientation_angle
        )
    
    def create_brace(self, label: str, start_node_id: int, end_node_id: int,
                    material_id: int, section_id: int, orientation_angle: float = 0.0) -> Element:
        
        # Braces typically have pinned connections
        releases = {
            "start": {"moment_y": True, "moment_z": True},
            "end": {"moment_y": True, "moment_z": True}
        }
        
        return self.create_element(
            label, ElementType.BRACE, start_node_id, end_node_id,
            material_id, section_id, orientation_angle, releases
        )
    
    def create_wall_elements(self, corner_nodes: List[int], material_id: int, 
                           section_id: int, mesh_size: float = 1.0) -> List[Element]:
        """Create wall elements from corner nodes"""
        if len(corner_nodes) < 3:
            raise ValueError("Wall requires at least 3 corner nodes")
        
        # For now, create as frame elements around the perimeter
        # In a full implementation, this would create shell elements
        elements = []
        
        for i in range(len(corner_nodes)):
            start_node = corner_nodes[i]
            end_node = corner_nodes[(i + 1) % len(corner_nodes)]
            
            label = f"W{len(self._elements_cache) + len(elements) + 1}"
            element = self.create_element(
                label, ElementType.WALL, start_node, end_node,
                material_id, section_id
            )
            elements.append(element)
        
        return elements
    
    def create_slab_elements(self, corner_nodes: List[int], material_id: int,
                           section_id: int, mesh_size: float = 1.0) -> List[Element]:
        """Create slab elements from corner nodes"""
        # This is a simplified implementation
        # Full implementation would create shell/plate elements
        elements = []
        
        # Create perimeter elements
        for i in range(len(corner_nodes)):
            start_node = corner_nodes[i]
            end_node = corner_nodes[(i + 1) % len(corner_nodes)]
            
            label = f"S{len(self._elements_cache) + len(elements) + 1}"
            element = self.create_element(
                label, ElementType.SLAB, start_node, end_node,
                material_id, section_id
            )
            elements.append(element)
        
        return elements
    
    def auto_connect_elements(self, tolerance: float = 0.001) -> int:
        """Automatically connect elements at common nodes"""
        connections_made = 0
        
        # This would be implemented to automatically connect elements
        # that share nodes within the tolerance
        
        return connections_made
    
    def get_element_connectivity_matrix(self) -> np.ndarray:
        """Get element connectivity matrix for analysis"""
        elements = self.get_all_elements()
        if not elements:
            return np.array([])
        
        # Create connectivity matrix [element_id, start_node_id, end_node_id]
        connectivity = np.zeros((len(elements), 3), dtype=int)
        
        for i, element in enumerate(elements):
            connectivity[i] = [element.id, element.start_node_id, element.end_node_id]
        
        return connectivity
