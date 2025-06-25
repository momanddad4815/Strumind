import json
import time
from typing import Dict, List, Any
from datetime import datetime


class IFCExporter:
    """IFC 4.x exporter for structural models"""
    
    def __init__(self):
        self.ifc_version = "IFC4"
        self.application_name = "StruMind"
        self.application_version = "1.0.0"
    
    def export_model(self, model_data: Dict, file_path: str, version: str = "IFC4") -> Dict[str, Any]:
        """Export structural model to IFC format"""
        
        start_time = time.time()
        
        try:
            # Generate IFC content
            ifc_content = self._generate_ifc_content(model_data, version)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ifc_content)
            
            export_time = time.time() - start_time
            
            return {
                "status": "success",
                "file_path": file_path,
                "version": version,
                "elements_exported": len(model_data.get("elements", [])),
                "export_time": export_time,
                "file_size": len(ifc_content)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "export_time": time.time() - start_time
            }
    
    def _generate_ifc_content(self, model_data: Dict, version: str) -> str:
        """Generate IFC file content"""
        
        lines = []
        entity_counter = 1
        
        # IFC Header
        lines.extend(self._generate_ifc_header(version))
        
        # IFC Data section
        lines.append("DATA;")
        
        # Create global entities
        entities = {}
        
        # Application and organization
        entities["application"] = entity_counter
        lines.append(f"#{entity_counter} = IFCAPPLICATION({self._ref(entities, 'organization')}, '{self.application_version}', '{self.application_name}', 'StruMind Structural Engineering Platform');")
        entity_counter += 1
        
        entities["organization"] = entity_counter
        lines.append(f"#{entity_counter} = IFCORGANIZATION($, 'StruMind Inc.', 'Structural Engineering Software', $, $);")
        entity_counter += 1
        
        # Person and ownership
        entities["person"] = entity_counter
        lines.append(f"#{entity_counter} = IFCPERSON($, 'System', 'Engineer', $, $, $, $, $);")
        entity_counter += 1
        
        entities["person_organization"] = entity_counter
        lines.append(f"#{entity_counter} = IFCPERSONANDORGANIZATION({self._ref(entities, 'person')}, {self._ref(entities, 'organization')}, $);")
        entity_counter += 1
        
        entities["owner_history"] = entity_counter
        timestamp = int(datetime.now().timestamp())
        lines.append(f"#{entity_counter} = IFCOWNERHISTORY({self._ref(entities, 'person_organization')}, {self._ref(entities, 'application')}, $, .ADDED., {timestamp}, {self._ref(entities, 'person_organization')}, {self._ref(entities, 'application')}, {timestamp});")
        entity_counter += 1
        
        # Units
        entities.update(self._create_units(entity_counter))
        entity_counter += 10  # Reserve space for units
        
        # Coordinate system
        entities["origin"] = entity_counter
        lines.append(f"#{entity_counter} = IFCCARTESIANPOINT((0., 0., 0.));")
        entity_counter += 1
        
        entities["x_axis"] = entity_counter
        lines.append(f"#{entity_counter} = IFCDIRECTION((1., 0., 0.));")
        entity_counter += 1
        
        entities["z_axis"] = entity_counter
        lines.append(f"#{entity_counter} = IFCDIRECTION((0., 0., 1.));")
        entity_counter += 1
        
        entities["placement"] = entity_counter
        lines.append(f"#{entity_counter} = IFCAXIS2PLACEMENT3D({self._ref(entities, 'origin')}, {self._ref(entities, 'z_axis')}, {self._ref(entities, 'x_axis')});")
        entity_counter += 1
        
        entities["geometric_context"] = entity_counter
        lines.append(f"#{entity_counter} = IFCGEOMETRICREPRESENTATIONCONTEXT($, 'Model', 3, 1.E-05, {self._ref(entities, 'placement')}, $);")
        entity_counter += 1
        
        # Project
        entities["project"] = entity_counter
        project_name = model_data.get("model_info", {}).get("model_name", "Structural Model")
        lines.append(f"#{entity_counter} = IFCPROJECT('{self._generate_guid()}', {self._ref(entities, 'owner_history')}, '{project_name}', 'Structural engineering model exported from StruMind', $, $, $, ({self._ref(entities, 'geometric_context')}), {self._ref(entities, 'unit_assignment')});")
        entity_counter += 1
        
        # Site
        entities["site"] = entity_counter
        lines.append(f"#{entity_counter} = IFCSITE('{self._generate_guid()}', {self._ref(entities, 'owner_history')}, 'Site', 'Building site', $, {self._ref(entities, 'placement')}, $, $, .ELEMENT., $, $, $, $, $);")
        entity_counter += 1
        
        # Building
        entities["building"] = entity_counter
        lines.append(f"#{entity_counter} = IFCBUILDING('{self._generate_guid()}', {self._ref(entities, 'owner_history')}, 'Building', 'Main building', $, {self._ref(entities, 'placement')}, $, $, .ELEMENT., $, $, $);")
        entity_counter += 1
        
        # Building storey
        entities["storey"] = entity_counter
        lines.append(f"#{entity_counter} = IFCBUILDINGSTOREY('{self._generate_guid()}', {self._ref(entities, 'owner_history')}, 'Ground Floor', 'Ground floor level', $, {self._ref(entities, 'placement')}, $, $, .ELEMENT., 0.);")
        entity_counter += 1
        
        # Materials
        material_entities = {}
        for material in model_data.get("materials", []):
            material_entities[material["id"]] = entity_counter
            lines.append(f"#{entity_counter} = IFCMATERIAL('{material['name']}');")
            entity_counter += 1
        
        # Create structural elements
        element_entities = {}
        for element in model_data.get("elements", []):
            element_entity, entity_counter = self._create_structural_element(
                element, model_data, entities, material_entities, entity_counter
            )
            element_entities[element["id"]] = element_entity
            lines.extend(element_entity["lines"])
        
        # Relationships
        lines.extend(self._create_relationships(entities, element_entities, entity_counter))
        
        lines.append("ENDSEC;")
        lines.append("END-ISO-10303-21;")
        
        return "\n".join(lines)
    
    def _generate_ifc_header(self, version: str) -> List[str]:
        """Generate IFC header section"""
        
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        return [
            "ISO-10303-21;",
            "HEADER;",
            f"FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'), '2;1');",
            f"FILE_NAME('model.ifc', '{timestamp}', ('StruMind System'), ('StruMind Inc.'), 'StruMind Structural Engineering Platform', 'StruMind 1.0.0', '');",
            f"FILE_SCHEMA(('{version}'));",
            "ENDSEC;"
        ]
    
    def _create_units(self, start_counter: int) -> Dict[str, int]:
        """Create unit definitions"""
        
        entities = {}
        counter = start_counter
        
        # Length unit (meter)
        entities["length_unit"] = counter
        counter += 1
        
        # Area unit (square meter)
        entities["area_unit"] = counter
        counter += 1
        
        # Volume unit (cubic meter)
        entities["volume_unit"] = counter
        counter += 1
        
        # Force unit (Newton)
        entities["force_unit"] = counter
        counter += 1
        
        # Unit assignment
        entities["unit_assignment"] = counter
        
        return entities
    
    def _create_structural_element(self, element: Dict, model_data: Dict, 
                                 global_entities: Dict, material_entities: Dict,
                                 entity_counter: int) -> tuple:
        """Create IFC structural element"""
        
        lines = []
        element_entities = {"lines": lines}
        
        # Get nodes
        nodes = {node["id"]: node for node in model_data.get("nodes", [])}
        start_node = nodes.get(element["start_node_id"])
        end_node = nodes.get(element["end_node_id"])
        
        if not start_node or not end_node:
            return element_entities, entity_counter
        
        # Create geometry
        start_point_id = entity_counter
        lines.append(f"#{entity_counter} = IFCCARTESIANPOINT(({start_node['x']}, {start_node['y']}, {start_node['z']}));")
        entity_counter += 1
        
        end_point_id = entity_counter
        lines.append(f"#{entity_counter} = IFCCARTESIANPOINT(({end_node['x']}, {end_node['y']}, {end_node['z']}));")
        entity_counter += 1
        
        # Create line
        line_id = entity_counter
        lines.append(f"#{entity_counter} = IFCLINE(#{start_point_id}, IFCVECTOR(IFCDIRECTION(({end_node['x'] - start_node['x']}, {end_node['y'] - start_node['y']}, {end_node['z'] - start_node['z']})), 1.0));")
        entity_counter += 1
        
        # Create curve
        curve_id = entity_counter
        lines.append(f"#{entity_counter} = IFCTRIMMEDCURVE(#{line_id}, (IFCPARAMETERVALUE(0.)), (IFCPARAMETERVALUE(1.)), .T., .PARAMETER.);")
        entity_counter += 1
        
        # Create representation
        geom_rep_id = entity_counter
        lines.append(f"#{entity_counter} = IFCSHAPEREPRESENTATION({self._ref(global_entities, 'geometric_context')}, 'Axis', 'Curve3D', (#{curve_id}));")
        entity_counter += 1
        
        product_rep_id = entity_counter
        lines.append(f"#{entity_counter} = IFCPRODUCTDEFINITIONSHAPE($, $, (#{geom_rep_id}));")
        entity_counter += 1
        
        # Determine IFC element type
        if element["type"] in ["beam"]:
            ifc_type = "IFCBEAM"
        elif element["type"] in ["column"]:
            ifc_type = "IFCCOLUMN"
        else:
            ifc_type = "IFCMEMBER"
        
        # Create structural element
        element_id = entity_counter
        lines.append(f"#{entity_counter} = {ifc_type}('{self._generate_guid()}', {self._ref(global_entities, 'owner_history')}, '{element['label']}', 'Structural {element['type']}', $, {self._ref(global_entities, 'placement')}, #{product_rep_id}, $);")
        entity_counter += 1
        
        element_entities["element_id"] = element_id
        element_entities["material_id"] = material_entities.get(element["material_id"])
        
        return element_entities, entity_counter
    
    def _create_relationships(self, global_entities: Dict, element_entities: Dict, entity_counter: int) -> List[str]:
        """Create IFC relationships"""
        
        lines = []
        
        # Project -> Site
        lines.append(f"#{entity_counter} = IFCRELAGGREGATES('{self._generate_guid()}', {self._ref(global_entities, 'owner_history')}, $, $, {self._ref(global_entities, 'project')}, ({self._ref(global_entities, 'site')}));")
        entity_counter += 1
        
        # Site -> Building
        lines.append(f"#{entity_counter} = IFCRELAGGREGATES('{self._generate_guid()}', {self._ref(global_entities, 'owner_history')}, $, $, {self._ref(global_entities, 'site')}, ({self._ref(global_entities, 'building')}));")
        entity_counter += 1
        
        # Building -> Storey
        lines.append(f"#{entity_counter} = IFCRELAGGREGATES('{self._generate_guid()}', {self._ref(global_entities, 'owner_history')}, $, $, {self._ref(global_entities, 'building')}, ({self._ref(global_entities, 'storey')}));")
        entity_counter += 1
        
        # Storey -> Elements
        element_ids = [str(elem["element_id"]) for elem in element_entities.values() if "element_id" in elem]
        if element_ids:
            lines.append(f"#{entity_counter} = IFCRELCONTAINEDINSPATIALSTRUCTURE('{self._generate_guid()}', {self._ref(global_entities, 'owner_history')}, $, $, ({', '.join(f'#{eid}' for eid in element_ids)}), {self._ref(global_entities, 'storey')});")
        
        return lines
    
    def _ref(self, entities: Dict, key: str) -> str:
        """Get entity reference"""
        return f"#{entities.get(key, 1)}"
    
    def _generate_guid(self) -> str:
        """Generate IFC GUID"""
        import uuid
        return str(uuid.uuid4()).replace('-', '').upper()[:22]
