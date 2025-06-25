from typing import List, Optional, Dict, Tuple
from backend.core.geometry import Point3D, GeometryUtils
from backend.db.models import Node, BoundaryCondition, SupportType
from sqlalchemy.orm import Session


class NodeManager:
    def __init__(self, db_session: Session, model_id: int):
        self.db = db_session
        self.model_id = model_id
        self._nodes_cache = {}
        self._load_nodes()
    
    def _load_nodes(self):
        nodes = self.db.query(Node).filter(Node.model_id == self.model_id).all()
        for node in nodes:
            self._nodes_cache[node.id] = node
    
    def create_node(self, label: str, x: float, y: float, z: float, snap_grid: float = None) -> Node:
        point = Point3D(x, y, z)
        
        # Apply grid snapping if specified
        if snap_grid:
            point = GeometryUtils.snap_to_grid(point, snap_grid)
        
        # Check for existing nodes at the same location
        existing_node = self.get_node_at_location(point.x, point.y, point.z, tolerance=0.001)
        if existing_node:
            return existing_node
        
        # Create new node
        node = Node(
            model_id=self.model_id,
            label=label,
            x=point.x,
            y=point.y,
            z=point.z
        )
        
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        
        self._nodes_cache[node.id] = node
        return node
    
    def get_node(self, node_id: int) -> Optional[Node]:
        return self._nodes_cache.get(node_id)
    
    def get_node_by_label(self, label: str) -> Optional[Node]:
        for node in self._nodes_cache.values():
            if node.label == label:
                return node
        return None
    
    def get_node_at_location(self, x: float, y: float, z: float, tolerance: float = 0.001) -> Optional[Node]:
        target_point = Point3D(x, y, z)
        for node in self._nodes_cache.values():
            node_point = Point3D(node.x, node.y, node.z)
            if target_point.distance_to(node_point) <= tolerance:
                return node
        return None
    
    def get_all_nodes(self) -> List[Node]:
        return list(self._nodes_cache.values())
    
    def update_node_position(self, node_id: int, x: float, y: float, z: float) -> bool:
        node = self.get_node(node_id)
        if not node:
            return False
        
        node.x = x
        node.y = y
        node.z = z
        
        self.db.commit()
        return True
    
    def delete_node(self, node_id: int) -> bool:
        node = self.get_node(node_id)
        if not node:
            return False
        
        # Check if node is used by elements
        elements_count = self.db.query(Element).filter(
            (Element.start_node_id == node_id) | (Element.end_node_id == node_id)
        ).count()
        
        if elements_count > 0:
            raise ValueError(f"Cannot delete node {node_id}: it is used by {elements_count} elements")
        
        self.db.delete(node)
        self.db.commit()
        
        if node_id in self._nodes_cache:
            del self._nodes_cache[node_id]
        
        return True
    
    def add_boundary_condition(self, node_id: int, support_type: SupportType, 
                             restrain_x: bool = False, restrain_y: bool = False, restrain_z: bool = False,
                             restrain_rx: bool = False, restrain_ry: bool = False, restrain_rz: bool = False,
                             spring_constants: Dict[str, float] = None) -> BoundaryCondition:
        
        node = self.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        # Remove existing boundary condition
        existing_bc = self.db.query(BoundaryCondition).filter(
            BoundaryCondition.node_id == node_id
        ).first()
        
        if existing_bc:
            self.db.delete(existing_bc)
        
        # Set default restraints based on support type
        if support_type == SupportType.FIXED:
            restrain_x = restrain_y = restrain_z = True
            restrain_rx = restrain_ry = restrain_rz = True
        elif support_type == SupportType.PINNED:
            restrain_x = restrain_y = restrain_z = True
            restrain_rx = restrain_ry = restrain_rz = False
        elif support_type == SupportType.ROLLER:
            restrain_z = True  # Vertical support only
        
        bc = BoundaryCondition(
            model_id=self.model_id,
            node_id=node_id,
            support_type=support_type,
            restrain_x=restrain_x,
            restrain_y=restrain_y,
            restrain_z=restrain_z,
            restrain_rx=restrain_rx,
            restrain_ry=restrain_ry,
            restrain_rz=restrain_rz
        )
        
        # Add spring constants if provided
        if spring_constants:
            bc.spring_kx = spring_constants.get('kx')
            bc.spring_ky = spring_constants.get('ky')
            bc.spring_kz = spring_constants.get('kz')
            bc.spring_krx = spring_constants.get('krx')
            bc.spring_kry = spring_constants.get('kry')
            bc.spring_krz = spring_constants.get('krz')
        
        self.db.add(bc)
        self.db.commit()
        
        return bc
    
    def get_boundary_condition(self, node_id: int) -> Optional[BoundaryCondition]:
        return self.db.query(BoundaryCondition).filter(
            BoundaryCondition.node_id == node_id
        ).first()
    
    def remove_boundary_condition(self, node_id: int) -> bool:
        bc = self.get_boundary_condition(node_id)
        if bc:
            self.db.delete(bc)
            self.db.commit()
            return True
        return False
    
    def generate_node_grid(self, x_range: Tuple[float, float], y_range: Tuple[float, float], 
                          z_range: Tuple[float, float], spacing: Tuple[float, float, float]) -> List[Node]:
        """Generate a grid of nodes"""
        nodes = []
        x_start, x_end = x_range
        y_start, y_end = y_range
        z_start, z_end = z_range
        x_spacing, y_spacing, z_spacing = spacing
        
        node_counter = len(self._nodes_cache) + 1
        
        x = x_start
        while x <= x_end:
            y = y_start
            while y <= y_end:
                z = z_start
                while z <= z_end:
                    label = f"N{node_counter}"
                    node = self.create_node(label, x, y, z)
                    nodes.append(node)
                    node_counter += 1
                    z += z_spacing
                y += y_spacing
            x += x_spacing
        
        return nodes
    
    def get_nodes_in_range(self, center: Point3D, radius: float) -> List[Node]:
        """Get all nodes within a specified radius from a center point"""
        nodes_in_range = []
        for node in self._nodes_cache.values():
            node_point = Point3D(node.x, node.y, node.z)
            if center.distance_to(node_point) <= radius:
                nodes_in_range.append(node)
        return nodes_in_range
