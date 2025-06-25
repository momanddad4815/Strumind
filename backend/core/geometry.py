import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class Point3D:
    x: float
    y: float
    z: float
    
    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def distance_to(self, other) -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])


@dataclass
class Vector3D:
    x: float
    y: float
    z: float
    
    def __add__(self, other):
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float):
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / mag, self.y / mag, self.z / mag)
    
    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])


class GeometryUtils:
    @staticmethod
    def calculate_element_length(start_point: Point3D, end_point: Point3D) -> float:
        return start_point.distance_to(end_point)
    
    @staticmethod
    def calculate_element_direction_cosines(start_point: Point3D, end_point: Point3D) -> Tuple[float, float, float]:
        vector = end_point - start_point
        length = vector.magnitude()
        if length == 0:
            return (1.0, 0.0, 0.0)
        
        normalized = vector.normalize()
        return (normalized.x, normalized.y, normalized.z)
    
    @staticmethod
    def calculate_local_coordinate_system(start_point: Point3D, end_point: Point3D, orientation_angle: float = 0.0):
        # Local x-axis (element axis)
        local_x = (end_point - start_point).normalize()
        
        # Local z-axis (vertical direction by default)
        global_z = Vector3D(0, 0, 1)
        
        # Check if element is vertical
        if abs(local_x.dot(global_z)) > 0.99:
            # Element is vertical, use global Y as reference
            local_y = Vector3D(0, 1, 0)
            local_z = local_x.cross(local_y).normalize()
            local_y = local_z.cross(local_x).normalize()
        else:
            # Element is not vertical
            local_z = local_x.cross(global_z).normalize()
            local_y = local_z.cross(local_x).normalize()
        
        # Apply orientation angle rotation about local x-axis
        if orientation_angle != 0.0:
            cos_angle = math.cos(math.radians(orientation_angle))
            sin_angle = math.sin(math.radians(orientation_angle))
            
            # Rotate local y and z axes
            new_local_y = Vector3D(
                local_y.x * cos_angle - local_z.x * sin_angle,
                local_y.y * cos_angle - local_z.y * sin_angle,
                local_y.z * cos_angle - local_z.z * sin_angle
            )
            
            new_local_z = Vector3D(
                local_y.x * sin_angle + local_z.x * cos_angle,
                local_y.y * sin_angle + local_z.y * cos_angle,
                local_y.z * sin_angle + local_z.z * cos_angle
            )
            
            local_y = new_local_y
            local_z = new_local_z
        
        # Return transformation matrix
        transformation_matrix = np.array([
            [local_x.x, local_x.y, local_x.z],
            [local_y.x, local_y.y, local_y.z],
            [local_z.x, local_z.y, local_z.z]
        ])
        
        return transformation_matrix
    
    @staticmethod
    def snap_to_grid(point: Point3D, grid_size: float) -> Point3D:
        return Point3D(
            round(point.x / grid_size) * grid_size,
            round(point.y / grid_size) * grid_size,
            round(point.z / grid_size) * grid_size
        )
    
    @staticmethod
    def snap_to_point(point: Point3D, target_points: List[Point3D], tolerance: float = 0.1) -> Optional[Point3D]:
        for target in target_points:
            if point.distance_to(target) <= tolerance:
                return target
        return None
    
    @staticmethod
    def snap_to_line(point: Point3D, line_start: Point3D, line_end: Point3D, tolerance: float = 0.1) -> Optional[Point3D]:
        # Calculate closest point on line
        line_vector = line_end - line_start
        point_vector = point - line_start
        
        line_length = line_vector.magnitude()
        if line_length == 0:
            return None
        
        # Project point onto line
        projection_length = point_vector.dot(line_vector) / line_length
        
        # Clamp to line segment
        if projection_length < 0:
            closest_point = line_start
        elif projection_length > line_length:
            closest_point = line_end
        else:
            normalized_line = line_vector.normalize()
            closest_point = line_start + Point3D(
                normalized_line.x * projection_length,
                normalized_line.y * projection_length,
                normalized_line.z * projection_length
            )
        
        if point.distance_to(closest_point) <= tolerance:
            return closest_point
        return None
