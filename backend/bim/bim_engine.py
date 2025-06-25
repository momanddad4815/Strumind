import os
import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from backend.core.model import StructuralModel
from backend.bim.ifc_exporter import IFCExporter
from backend.bim.gltf_exporter import GLTFExporter
from backend.bim.dxf_exporter import DXFExporter
from backend.db.models import BIMData
import logging
from datetime import datetime


class BIMEngine:
    """Main BIM engine that coordinates export/import operations"""
    
    def __init__(self, structural_model: StructuralModel):
        self.model = structural_model
        self.db = structural_model.db
        
        # BIM exporters
        self.ifc_exporter = IFCExporter()
        self.gltf_exporter = GLTFExporter()
        self.dxf_exporter = DXFExporter()
        
        # Results storage
        self.export_results = {}
    
    def export_to_ifc(self, file_path: str = None, version: str = "IFC4") -> Dict[str, Any]:
        """Export model to IFC format"""
        
        try:
            # Get model data
            model_data = self.model.export_model_data()
            
            # Generate file path if not provided
            if not file_path:
                model_name = self.model.model.name.replace(" ", "_")
                file_path = f"exports/{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ifc"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Export to IFC
            result = self.ifc_exporter.export_model(model_data, file_path, version)
            
            if result["status"] == "success":
                # Store BIM data record
                bim_data = BIMData(
                    model_id=self.model.model.id,
                    file_format="ifc",
                    file_path=file_path,
                    file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(bim_data)
                self.db.commit()
                
                complete_result = {
                    "status": "success",
                    "format": "IFC",
                    "version": version,
                    "file_path": file_path,
                    "file_size": bim_data.file_size,
                    "elements_exported": result.get("elements_exported", 0),
                    "export_time": result.get("export_time", 0),
                    "bim_data_id": bim_data.id
                }
                
                self.export_results["ifc"] = complete_result
                logging.info(f"IFC export completed: {file_path}")
                
                return complete_result
            
            else:
                return result
                
        except Exception as e:
            logging.error(f"IFC export failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def export_to_gltf(self, file_path: str = None, include_materials: bool = True,
                      include_analysis_results: bool = False) -> Dict[str, Any]:
        """Export model to glTF format for web visualization"""
        
        try:
            # Get model data
            model_data = self.model.export_model_data()
            
            # Get analysis results if requested
            analysis_data = None
            if include_analysis_results:
                from backend.db.models import AnalysisResult
                latest_analysis = self.db.query(AnalysisResult).filter(
                    AnalysisResult.model_id == self.model.model.id,
                    AnalysisResult.status == "completed"
                ).order_by(AnalysisResult.completed_at.desc()).first()
                
                if latest_analysis:
                    analysis_data = {
                        "type": latest_analysis.analysis_type,
                        "displacements": latest_analysis.node_displacements,
                        "forces": latest_analysis.element_forces
                    }
            
            # Generate file path if not provided
            if not file_path:
                model_name = self.model.model.name.replace(" ", "_")
                file_path = f"exports/{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gltf"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Export to glTF
            result = self.gltf_exporter.export_model(
                model_data, file_path, include_materials, analysis_data
            )
            
            if result["status"] == "success":
                # Store BIM data record
                bim_data = BIMData(
                    model_id=self.model.model.id,
                    file_format="gltf",
                    file_path=file_path,
                    file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(bim_data)
                self.db.commit()
                
                complete_result = {
                    "status": "success",
                    "format": "glTF",
                    "file_path": file_path,
                    "file_size": bim_data.file_size,
                    "elements_exported": result.get("elements_exported", 0),
                    "include_materials": include_materials,
                    "include_analysis": include_analysis_results,
                    "export_time": result.get("export_time", 0),
                    "bim_data_id": bim_data.id
                }
                
                self.export_results["gltf"] = complete_result
                logging.info(f"glTF export completed: {file_path}")
                
                return complete_result
            
            else:
                return result
                
        except Exception as e:
            logging.error(f"glTF export failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def export_to_dxf(self, file_path: str = None, view_type: str = "plan",
                     include_dimensions: bool = True, include_annotations: bool = True) -> Dict[str, Any]:
        """Export model to DXF format for CAD integration"""
        
        try:
            # Get model data
            model_data = self.model.export_model_data()
            
            # Generate file path if not provided
            if not file_path:
                model_name = self.model.model.name.replace(" ", "_")
                file_path = f"exports/{model_name}_{view_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dxf"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Export to DXF
            result = self.dxf_exporter.export_model(
                model_data, file_path, view_type, include_dimensions, include_annotations
            )
            
            if result["status"] == "success":
                # Store BIM data record
                bim_data = BIMData(
                    model_id=self.model.model.id,
                    file_format="dxf",
                    file_path=file_path,
                    file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(bim_data)
                self.db.commit()
                
                complete_result = {
                    "status": "success",
                    "format": "DXF",
                    "file_path": file_path,
                    "file_size": bim_data.file_size,
                    "view_type": view_type,
                    "include_dimensions": include_dimensions,
                    "include_annotations": include_annotations,
                    "elements_exported": result.get("elements_exported", 0),
                    "export_time": result.get("export_time", 0),
                    "bim_data_id": bim_data.id
                }
                
                self.export_results["dxf"] = complete_result
                logging.info(f"DXF export completed: {file_path}")
                
                return complete_result
            
            else:
                return result
                
        except Exception as e:
            logging.error(f"DXF export failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_export_history(self) -> List[Dict[str, Any]]:
        """Get history of BIM exports"""
        
        bim_exports = self.db.query(BIMData).filter(
            BIMData.model_id == self.model.model.id
        ).order_by(BIMData.created_at.desc()).all()
        
        return [
            {
                "id": export.id,
                "file_format": export.file_format,
                "file_path": export.file_path,
                "file_size": export.file_size,
                "created_at": export.created_at,
                "file_exists": os.path.exists(export.file_path) if export.file_path else False
            }
            for export in bim_exports
        ]
    
    def get_model_for_web_viewer(self) -> Dict[str, Any]:
        """Get optimized model data for web 3D viewer"""
        
        try:
            # Get model data
            model_data = self.model.export_model_data()
            
            # Simplify for web viewer
            web_model = {
                "nodes": [],
                "elements": [],
                "materials": {},
                "analysis_results": None
            }
            
            # Process nodes
            for node in model_data["nodes"]:
                web_model["nodes"].append({
                    "id": node["id"],
                    "label": node["label"],
                    "position": [node["x"], node["y"], node["z"]]
                })
            
            # Process elements
            for element in model_data["elements"]:
                material_id = element["material_id"]
                material_info = next((m for m in model_data["materials"] if m["id"] == material_id), None)
                
                web_model["elements"].append({
                    "id": element["id"],
                    "label": element["label"],
                    "type": element["type"],
                    "start_node": element["start_node_id"],
                    "end_node": element["end_node_id"],
                    "material_type": material_info["type"] if material_info else "unknown",
                    "section_id": element["section_id"]
                })
            
            # Process materials (simplified)
            material_colors = {
                "concrete": "#808080",
                "steel": "#B87333",
                "timber": "#8B4513"
            }
            
            for material in model_data["materials"]:
                web_model["materials"][material["id"]] = {
                    "name": material["name"],
                    "type": material["type"],
                    "color": material_colors.get(material["type"], "#808080")
                }
            
            # Get latest analysis results
            from backend.db.models import AnalysisResult
            latest_analysis = self.db.query(AnalysisResult).filter(
                AnalysisResult.model_id == self.model.model.id,
                AnalysisResult.status == "completed"
            ).order_by(AnalysisResult.completed_at.desc()).first()
            
            if latest_analysis:
                web_model["analysis_results"] = {
                    "type": latest_analysis.analysis_type,
                    "displacements": latest_analysis.node_displacements,
                    "max_displacement": self._get_max_displacement(latest_analysis.node_displacements)
                }
            
            return {
                "status": "success",
                "model": web_model,
                "metadata": {
                    "model_name": self.model.model.name,
                    "units": self.model.model.units,
                    "total_nodes": len(web_model["nodes"]),
                    "total_elements": len(web_model["elements"]),
                    "last_modified": self.model.model.updated_at
                }
            }
            
        except Exception as e:
            logging.error(f"Web viewer model generation failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _get_max_displacement(self, displacements: Dict) -> float:
        """Calculate maximum displacement magnitude"""
        max_disp = 0
        
        if displacements:
            for node_disp in displacements.values():
                if isinstance(node_disp, dict):
                    ux = node_disp.get("ux", 0)
                    uy = node_disp.get("uy", 0)
                    uz = node_disp.get("uz", 0)
                    magnitude = (ux**2 + uy**2 + uz**2)**0.5
                    max_disp = max(max_disp, magnitude)
        
        return max_disp
    
    def clear_export_files(self, older_than_days: int = 30):
        """Clear old export files"""
        
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        old_exports = self.db.query(BIMData).filter(
            BIMData.model_id == self.model.model.id,
            BIMData.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for export in old_exports:
            if export.file_path and os.path.exists(export.file_path):
                try:
                    os.remove(export.file_path)
                    deleted_count += 1
                except OSError:
                    pass
            
            self.db.delete(export)
        
        self.db.commit()
        
        logging.info(f"Cleared {deleted_count} old export files")
        return {"deleted_files": deleted_count}
    
    def export_drawing_package(self, output_dir: str = None) -> Dict[str, Any]:
        """Export complete drawing package (multiple formats)"""
        
        try:
            if not output_dir:
                model_name = self.model.model.name.replace(" ", "_")
                output_dir = f"exports/{model_name}_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            os.makedirs(output_dir, exist_ok=True)
            
            results = {}
            
            # Export IFC
            ifc_path = os.path.join(output_dir, "model.ifc")
            results["ifc"] = self.export_to_ifc(ifc_path)
            
            # Export glTF for web
            gltf_path = os.path.join(output_dir, "model.gltf")
            results["gltf"] = self.export_to_gltf(gltf_path, include_analysis_results=True)
            
            # Export DXF plans
            plan_path = os.path.join(output_dir, "plan.dxf")
            results["dxf_plan"] = self.export_to_dxf(plan_path, "plan")
            
            # Export DXF elevation
            elevation_path = os.path.join(output_dir, "elevation.dxf")
            results["dxf_elevation"] = self.export_to_dxf(elevation_path, "elevation")
            
            # Create summary report
            summary = {
                "package_created": datetime.utcnow(),
                "model_name": self.model.model.name,
                "output_directory": output_dir,
                "exports": results,
                "total_files": len([r for r in results.values() if r.get("status") == "success"])
            }
            
            # Save summary as JSON
            summary_path = os.path.join(output_dir, "export_summary.json")
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2, default=str)
            
            return {
                "status": "success",
                "output_directory": output_dir,
                "summary": summary
            }
            
        except Exception as e:
            logging.error(f"Drawing package export failed: {str(e)}")
            return {"status": "error", "message": str(e)}
