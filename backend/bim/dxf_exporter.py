import time
from typing import Dict, List, Any


class DXFExporter:
    """DXF exporter for CAD integration"""
    
    def __init__(self):
        self.dxf_version = "AC1027"  # AutoCAD 2013
        self.application_name = "StruMind"
    
    def export_model(self, model_data: Dict, file_path: str, view_type: str = "plan",
                    include_dimensions: bool = True, include_annotations: bool = True) -> Dict[str, Any]:
        """Export structural model to DXF format"""
        
        start_time = time.time()
        
        try:
            # Generate DXF content
            dxf_content = self._generate_dxf_content(
                model_data, view_type, include_dimensions, include_annotations
            )
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            export_time = time.time() - start_time
            
            return {
                "status": "success",
                "file_path": file_path,
                "view_type": view_type,
                "elements_exported": len(model_data.get("elements", [])),
                "include_dimensions": include_dimensions,
                "include_annotations": include_annotations,
                "export_time": export_time
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "export_time": time.time() - start_time
            }
    
    def _generate_dxf_content(self, model_data: Dict, view_type: str,
                             include_dimensions: bool, include_annotations: bool) -> str:
        """Generate DXF file content"""
        
        lines = []
        
        # DXF Header
        lines.extend(self._generate_dxf_header())
        
        # Classes section
        lines.extend(self._generate_classes_section())
        
        # Tables section
        lines.extend(self._generate_tables_section())
        
        # Blocks section
        lines.extend(self._generate_blocks_section())
        
        # Entities section
        lines.extend(self._generate_entities_section(
            model_data, view_type, include_dimensions, include_annotations
        ))
        
        # Objects section
        lines.extend(self._generate_objects_section())
        
        # End of file
        lines.append("0")
        lines.append("EOF")
        
        return "\n".join(lines)
    
    def _generate_dxf_header(self) -> List[str]:
        """Generate DXF header section"""
        
        return [
            "0",
            "SECTION",
            "2",
            "HEADER",
            "9",
            "$ACADVER",
            "1",
            self.dxf_version,
            "9",
            "$DWGCODEPAGE",
            "3",
            "ANSI_1252",
            "9",
            "$INSBASE",
            "10",
            "0.0",
            "20",
            "0.0",
            "30",
            "0.0",
            "9",
            "$EXTMIN",
            "10",
            "0.0",
            "20",
            "0.0",
            "30",
            "0.0",
            "9",
            "$EXTMAX",
            "10",
            "100.0",
            "20",
            "100.0",
            "30",
            "100.0",
            "0",
            "ENDSEC"
        ]
    
    def _generate_classes_section(self) -> List[str]:
        """Generate DXF classes section"""
        
        return [
            "0",
            "SECTION",
            "2",
            "CLASSES",
            "0",
            "ENDSEC"
        ]
    
    def _generate_tables_section(self) -> List[str]:
        """Generate DXF tables section"""
        
        return [
            "0",
            "SECTION",
            "2",
            "TABLES",
            # Layer table
            "0",
            "TABLE",
            "2",
            "LAYER",
            "5",
            "2",
            "100",
            "AcDbSymbolTable",
            "70",
            "4",
            # Layer 0 (default)
            "0",
            "LAYER",
            "5",
            "10",
            "100",
            "AcDbSymbolTableRecord",
            "100",
            "AcDbLayerTableRecord",
            "2",
            "0",
            "70",
            "0",
            "62",
            "7",
            "6",
            "CONTINUOUS",
            # Structural layers
            "0",
            "LAYER",
            "5",
            "11",
            "100",
            "AcDbSymbolTableRecord",
            "100",
            "AcDbLayerTableRecord",
            "2",
            "BEAMS",
            "70",
            "0",
            "62",
            "1",  # Red
            "6",
            "CONTINUOUS",
            "0",
            "LAYER",
            "5",
            "12",
            "100",
            "AcDbSymbolTableRecord",
            "100",
            "AcDbLayerTableRecord",
            "2",
            "COLUMNS",
            "70",
            "0",
            "62",
            "3",  # Green
            "6",
            "CONTINUOUS",
            "0",
            "LAYER",
            "5",
            "13",
            "100",
            "AcDbSymbolTableRecord",
            "100",
            "AcDbLayerTableRecord",
            "2",
            "DIMENSIONS",
            "70",
            "0",
            "62",
            "4",  # Cyan
            "6",
            "CONTINUOUS",
            "0",
            "LAYER",
            "5",
            "14",
            "100",
            "AcDbSymbolTableRecord",
            "100",
            "AcDbLayerTableRecord",
            "2",
            "TEXT",
            "70",
            "0",
            "62",
            "2",  # Yellow
            "6",
            "CONTINUOUS",
            "0",
            "ENDTAB",
            "0",
            "ENDSEC"
        ]
    
    def _generate_blocks_section(self) -> List[str]:
        """Generate DXF blocks section"""
        
        return [
            "0",
            "SECTION",
            "2",
            "BLOCKS",
            "0",
            "ENDSEC"
        ]
    
    def _generate_entities_section(self, model_data: Dict, view_type: str,
                                  include_dimensions: bool, include_annotations: bool) -> List[str]:
        """Generate DXF entities section"""
        
        lines = [
            "0",
            "SECTION",
            "2",
            "ENTITIES"
        ]
        
        nodes = {node["id"]: node for node in model_data.get("nodes", [])}
        
        # Draw structural elements
        for element in model_data.get("elements", []):
            start_node = nodes.get(element["start_node_id"])
            end_node = nodes.get(element["end_node_id"])
            
            if not start_node or not end_node:
                continue
            
            # Project coordinates based on view type
            start_coords = self._project_coordinates(start_node, view_type)
            end_coords = self._project_coordinates(end_node, view_type)
            
            # Determine layer based on element type
            layer = self._get_element_layer(element["type"])
            
            # Create line entity
            lines.extend(self._create_line_entity(start_coords, end_coords, layer))
        
        # Add node markers (circles)
        for node in model_data.get("nodes", []):
            coords = self._project_coordinates(node, view_type)
            lines.extend(self._create_circle_entity(coords, 0.1, "0"))
        
        # Add dimensions if requested
        if include_dimensions:
            lines.extend(self._create_dimension_entities(model_data, view_type))
        
        # Add annotations if requested
        if include_annotations:
            lines.extend(self._create_annotation_entities(model_data, view_type))
        
        lines.extend([
            "0",
            "ENDSEC"
        ])
        
        return lines
    
    def _project_coordinates(self, node: Dict, view_type: str) -> tuple:
        """Project 3D coordinates to 2D based on view type"""
        
        x, y, z = node["x"], node["y"], node["z"]
        
        if view_type == "plan":
            return (x, y)
        elif view_type == "elevation":
            return (x, z)
        elif view_type == "section":
            return (y, z)
        else:
            return (x, y)  # Default to plan
    
    def _get_element_layer(self, element_type: str) -> str:
        """Get layer name for element type"""
        
        layer_map = {
            "beam": "BEAMS",
            "column": "COLUMNS",
            "brace": "BEAMS",
            "wall": "BEAMS",
            "slab": "BEAMS"
        }
        
        return layer_map.get(element_type, "0")
    
    def _create_line_entity(self, start_coords: tuple, end_coords: tuple, layer: str) -> List[str]:
        """Create DXF line entity"""
        
        return [
            "0",
            "LINE",
            "5",
            f"{hash(f'{start_coords}{end_coords}') % 1000000:06X}",
            "100",
            "AcDbEntity",
            "8",
            layer,
            "100",
            "AcDbLine",
            "10",
            str(start_coords[0]),
            "20",
            str(start_coords[1]),
            "30",
            "0.0",
            "11",
            str(end_coords[0]),
            "21",
            str(end_coords[1]),
            "31",
            "0.0"
        ]
    
    def _create_circle_entity(self, center_coords: tuple, radius: float, layer: str) -> List[str]:
        """Create DXF circle entity"""
        
        return [
            "0",
            "CIRCLE",
            "5",
            f"{hash(f'{center_coords}') % 1000000:06X}",
            "100",
            "AcDbEntity",
            "8",
            layer,
            "100",
            "AcDbCircle",
            "10",
            str(center_coords[0]),
            "20",
            str(center_coords[1]),
            "30",
            "0.0",
            "40",
            str(radius)
        ]
    
    def _create_dimension_entities(self, model_data: Dict, view_type: str) -> List[str]:
        """Create dimension entities"""
        
        lines = []
        
        # Simple grid dimensions (example)
        nodes = list(model_data.get("nodes", []))
        if len(nodes) >= 2:
            # Add overall dimension
            node1 = nodes[0]
            node2 = nodes[-1]
            
            coord1 = self._project_coordinates(node1, view_type)
            coord2 = self._project_coordinates(node2, view_type)
            
            # Calculate dimension
            distance = ((coord2[0] - coord1[0])**2 + (coord2[1] - coord1[1])**2)**0.5
            
            # Add dimension text
            mid_x = (coord1[0] + coord2[0]) / 2
            mid_y = (coord1[1] + coord2[1]) / 2 + 1.0  # Offset above
            
            lines.extend(self._create_text_entity(
                (mid_x, mid_y), f"{distance:.2f}", "DIMENSIONS"
            ))
        
        return lines
    
    def _create_annotation_entities(self, model_data: Dict, view_type: str) -> List[str]:
        """Create annotation entities"""
        
        lines = []
        
        # Add element labels
        nodes = {node["id"]: node for node in model_data.get("nodes", [])}
        
        for element in model_data.get("elements", []):
            start_node = nodes.get(element["start_node_id"])
            end_node = nodes.get(element["end_node_id"])
            
            if start_node and end_node:
                # Calculate midpoint
                start_coords = self._project_coordinates(start_node, view_type)
                end_coords = self._project_coordinates(end_node, view_type)
                
                mid_x = (start_coords[0] + end_coords[0]) / 2
                mid_y = (start_coords[1] + end_coords[1]) / 2
                
                # Add element label
                lines.extend(self._create_text_entity(
                    (mid_x, mid_y), element["label"], "TEXT"
                ))
        
        return lines
    
    def _create_text_entity(self, position: tuple, text: str, layer: str) -> List[str]:
        """Create DXF text entity"""
        
        return [
            "0",
            "TEXT",
            "5",
            f"{hash(f'{position}{text}') % 1000000:06X}",
            "100",
            "AcDbEntity",
            "8",
            layer,
            "100",
            "AcDbText",
            "10",
            str(position[0]),
            "20",
            str(position[1]),
            "30",
            "0.0",
            "40",
            "0.2",  # Text height
            "1",
            text,
            "50",
            "0.0",  # Rotation angle
            "100",
            "AcDbText"
        ]
    
    def _generate_objects_section(self) -> List[str]:
        """Generate DXF objects section"""
        
        return [
            "0",
            "SECTION",
            "2",
            "OBJECTS",
            "0",
            "DICTIONARY",
            "5",
            "C",
            "100",
            "AcDbDictionary",
            "281",
            "1",
            "3",
            "ACAD_GROUP",
            "350",
            "D",
            "0",
            "DICTIONARY",
            "5",
            "D",
            "100",
            "AcDbDictionary",
            "281",
            "1",
            "0",
            "ENDSEC"
        ]
