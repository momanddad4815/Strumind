import json
import time
import struct
import base64
from typing import Dict, List, Any, Optional
import numpy as np


class GLTFExporter:
    """glTF 2.0 exporter for web 3D visualization"""
    
    def __init__(self):
        self.gltf_version = "2.0"
        self.generator = "StruMind BIM Engine 1.0.0"
    
    def export_model(self, model_data: Dict, file_path: str, include_materials: bool = True,
                    analysis_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Export structural model to glTF format"""
        
        start_time = time.time()
        
        try:
            # Generate glTF content
            gltf_content = self._generate_gltf_content(model_data, include_materials, analysis_data)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(gltf_content, f, indent=2)
            
            export_time = time.time() - start_time
            
            return {
                "status": "success",
                "file_path": file_path,
                "format": "glTF 2.0",
                "elements_exported": len(model_data.get("elements", [])),
                "include_materials": include_materials,
                "include_analysis": analysis_data is not None,
                "export_time": export_time
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "export_time": time.time() - start_time
            }
    
    def _generate_gltf_content(self, model_data: Dict, include_materials: bool,
                              analysis_data: Optional[Dict]) -> Dict[str, Any]:
        """Generate glTF JSON content"""
        
        gltf = {
            "asset": {
                "version": self.gltf_version,
                "generator": self.generator,
                "copyright": "StruMind Inc."
            },
            "scene": 0,
            "scenes": [
                {
                    "name": "Structural Model",
                    "nodes": []
                }
            ],
            "nodes": [],
            "meshes": [],
            "buffers": [],
            "bufferViews": [],
            "accessors": []
        }
        
        # Add materials if requested
        if include_materials:
            gltf["materials"] = self._create_materials(model_data)
        
        # Create geometry data
        vertices, indices, element_info = self._create_geometry_data(model_data, analysis_data)
        
        if not vertices:
            # Create empty scene
            return gltf
        
        # Create buffer with vertex and index data
        buffer_data = self._create_buffer_data(vertices, indices)
        
        # Add buffer
        buffer_uri = self._encode_buffer_data(buffer_data)
        gltf["buffers"] = [
            {
                "uri": buffer_uri,
                "byteLength": len(buffer_data)
            }
        ]
        
        # Add buffer views
        gltf["bufferViews"] = self._create_buffer_views(vertices, indices)
        
        # Add accessors
        gltf["accessors"] = self._create_accessors(len(vertices), len(indices))
        
        # Create meshes for different element types
        meshes_created = 0
        for element_type in ["beam", "column", "brace"]:
            type_elements = [e for e in element_info if e["type"] == element_type]
            if type_elements:
                mesh = self._create_element_mesh(element_type, include_materials)
                gltf["meshes"].append(mesh)
                
                # Create node for this mesh
                node = {
                    "name": f"{element_type.title()} Elements",
                    "mesh": meshes_created
                }
                gltf["nodes"].append(node)
                gltf["scenes"][0]["nodes"].append(meshes_created)
                meshes_created += 1
        
        # Add nodes (structural nodes) as small spheres
        if model_data.get("nodes"):
            node_mesh = self._create_node_mesh(model_data["nodes"])
            gltf["meshes"].append(node_mesh)
            
            node_node = {
                "name": "Structural Nodes",
                "mesh": meshes_created
            }
            gltf["nodes"].append(node_node)
            gltf["scenes"][0]["nodes"].append(meshes_created)
        
        # Add analysis results as custom properties
        if analysis_data:
            gltf["extras"] = {
                "strumind_analysis": {
                    "type": analysis_data.get("type"),
                    "max_displacement": self._get_max_displacement(analysis_data.get("displacements", {})),
                    "has_displacements": bool(analysis_data.get("displacements")),
                    "has_forces": bool(analysis_data.get("forces"))
                }
            }
        
        return gltf
    
    def _create_materials(self, model_data: Dict) -> List[Dict[str, Any]]:
        """Create glTF materials"""
        
        materials = []
        material_colors = {
            "concrete": [0.5, 0.5, 0.5, 1.0],  # Gray
            "steel": [0.7, 0.45, 0.2, 1.0],    # Brown
            "timber": [0.55, 0.27, 0.07, 1.0], # Dark brown
            "composite": [0.4, 0.6, 0.8, 1.0]  # Blue
        }
        
        for material in model_data.get("materials", []):
            mat_type = material.get("type", "unknown")
            color = material_colors.get(mat_type, [0.5, 0.5, 0.5, 1.0])
            
            gltf_material = {
                "name": material["name"],
                "pbrMetallicRoughness": {
                    "baseColorFactor": color,
                    "metallicFactor": 0.1 if mat_type == "steel" else 0.0,
                    "roughnessFactor": 0.8
                },
                "extras": {
                    "strumind_material": {
                        "type": mat_type,
                        "elastic_modulus": material.get("elastic_modulus"),
                        "density": material.get("density")
                    }
                }
            }
            
            materials.append(gltf_material)
        
        return materials
    
    def _create_geometry_data(self, model_data: Dict, analysis_data: Optional[Dict]) -> tuple:
        """Create vertex and index data for structural elements"""
        
        vertices = []
        indices = []
        element_info = []
        
        nodes = {node["id"]: node for node in model_data.get("nodes", [])}
        
        # Get displacement data if available
        displacements = {}
        displacement_scale = 1.0
        if analysis_data and analysis_data.get("displacements"):
            displacements = analysis_data["displacements"]
            max_disp = self._get_max_displacement(displacements)
            if max_disp > 0:
                # Scale displacements for visualization (max 10% of model size)
                model_size = self._estimate_model_size(nodes)
                displacement_scale = (model_size * 0.1) / max_disp
        
        vertex_index = 0
        
        for element in model_data.get("elements", []):
            start_node = nodes.get(element["start_node_id"])
            end_node = nodes.get(element["end_node_id"])
            
            if not start_node or not end_node:
                continue
            
            # Get displaced positions if available
            start_pos = self._get_node_position(start_node, displacements, displacement_scale)
            end_pos = self._get_node_position(end_node, displacements, displacement_scale)
            
            # Create line geometry (simple cylinder would be better for full 3D)
            vertices.extend([
                start_pos[0], start_pos[1], start_pos[2],  # Start vertex
                end_pos[0], end_pos[1], end_pos[2]         # End vertex
            ])
            
            # Line indices
            indices.extend([vertex_index, vertex_index + 1])
            vertex_index += 2
            
            element_info.append({
                "id": element["id"],
                "type": element["type"],
                "start_vertex": vertex_index - 2,
                "end_vertex": vertex_index - 1
            })
        
        return vertices, indices, element_info
    
    def _get_node_position(self, node: Dict, displacements: Dict, scale: float) -> List[float]:
        """Get node position with optional displacement"""
        
        base_pos = [node["x"], node["y"], node["z"]]
        
        if displacements and str(node["id"]) in displacements:
            disp = displacements[str(node["id"])]
            if isinstance(disp, dict):
                dx = disp.get("ux", 0) * scale
                dy = disp.get("uy", 0) * scale
                dz = disp.get("uz", 0) * scale
                
                base_pos[0] += dx
                base_pos[1] += dy
                base_pos[2] += dz
        
        return base_pos
    
    def _get_max_displacement(self, displacements: Dict) -> float:
        """Calculate maximum displacement magnitude"""
        
        max_disp = 0
        for node_disp in displacements.values():
            if isinstance(node_disp, dict):
                ux = node_disp.get("ux", 0)
                uy = node_disp.get("uy", 0)
                uz = node_disp.get("uz", 0)
                magnitude = (ux**2 + uy**2 + uz**2)**0.5
                max_disp = max(max_disp, magnitude)
        
        return max_disp
    
    def _estimate_model_size(self, nodes: Dict) -> float:
        """Estimate overall model size"""
        
        if not nodes:
            return 1.0
        
        positions = [[node["x"], node["y"], node["z"]] for node in nodes.values()]
        positions = np.array(positions)
        
        min_coords = np.min(positions, axis=0)
        max_coords = np.max(positions, axis=0)
        
        return np.linalg.norm(max_coords - min_coords)
    
    def _create_buffer_data(self, vertices: List[float], indices: List[int]) -> bytes:
        """Create binary buffer data"""
        
        buffer_data = b""
        
        # Vertex data (float32)
        for vertex in vertices:
            buffer_data += struct.pack('<f', vertex)
        
        # Align to 4-byte boundary
        while len(buffer_data) % 4 != 0:
            buffer_data += b'\x00'
        
        # Index data (uint16)
        for index in indices:
            buffer_data += struct.pack('<H', index)
        
        # Align to 4-byte boundary
        while len(buffer_data) % 4 != 0:
            buffer_data += b'\x00'
        
        return buffer_data
    
    def _encode_buffer_data(self, buffer_data: bytes) -> str:
        """Encode buffer data as data URI"""
        
        encoded = base64.b64encode(buffer_data).decode('ascii')
        return f"data:application/octet-stream;base64,{encoded}"
    
    def _create_buffer_views(self, vertices: List[float], indices: List[int]) -> List[Dict[str, Any]]:
        """Create glTF buffer views"""
        
        vertex_byte_length = len(vertices) * 4  # float32
        
        return [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": vertex_byte_length,
                "target": 34962  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": ((vertex_byte_length + 3) // 4) * 4,  # Aligned offset
                "byteLength": len(indices) * 2,  # uint16
                "target": 34963  # ELEMENT_ARRAY_BUFFER
            }
        ]
    
    def _create_accessors(self, vertex_count: int, index_count: int) -> List[Dict[str, Any]]:
        """Create glTF accessors"""
        
        return [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": vertex_count // 3,
                "type": "VEC3",
                "name": "POSITION"
            },
            {
                "bufferView": 1,
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": index_count,
                "type": "SCALAR",
                "name": "INDICES"
            }
        ]
    
    def _create_element_mesh(self, element_type: str, include_materials: bool) -> Dict[str, Any]:
        """Create mesh for specific element type"""
        
        mesh = {
            "name": f"{element_type.title()} Elements",
            "primitives": [
                {
                    "attributes": {
                        "POSITION": 0
                    },
                    "indices": 1,
                    "mode": 1  # LINES
                }
            ]
        }
        
        # Add material if requested
        if include_materials:
            material_map = {"beam": 0, "column": 0, "brace": 0}
            mesh["primitives"][0]["material"] = material_map.get(element_type, 0)
        
        return mesh
    
    def _create_node_mesh(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Create mesh for structural nodes"""
        
        return {
            "name": "Structural Nodes",
            "primitives": [
                {
                    "attributes": {
                        "POSITION": 0
                    },
                    "mode": 0  # POINTS
                }
            ]
        }
