from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from core.model import StructuralModel
from design.rc_design import RCDesigner
from design.steel_design import SteelDesigner
from db.models import DesignResult, Element, Material, Section
import logging
from datetime import datetime


class DesignEngine:
    """Main design engine that coordinates all design types"""
    
    def __init__(self, structural_model: StructuralModel):
        self.model = structural_model
        self.db = structural_model.db
        
        # Design components
        self.rc_designer = None
        self.steel_designer = None
        
        # Results storage
        self.design_results = {}
    
    def run_rc_design(self, design_code: str = "IS456", element_ids: List[int] = None) -> Dict[str, Any]:
        """Run reinforced concrete design"""
        
        try:
            # Initialize RC designer
            self.rc_designer = RCDesigner(design_code)
            
            # Get elements to design
            if element_ids:
                elements = [self.model.element_manager.get_element(eid) for eid in element_ids]
                elements = [e for e in elements if e is not None]
            else:
                # Get all concrete elements
                all_elements = self.model.element_manager.get_all_elements()
                materials = {m.id: m for m in self.model.material_manager.get_all_materials()}
                elements = [e for e in all_elements if materials[e.material_id].material_type == "concrete"]
            
            if not elements:
                return {"status": "failed", "error": "No concrete elements found for design"}
            
            # Get latest analysis results
            from db.models import AnalysisResult
            latest_analysis = self.db.query(AnalysisResult).filter(
                AnalysisResult.model_id == self.model.model.id,
                AnalysisResult.analysis_type == "linear_static",
                AnalysisResult.status == "completed"
            ).order_by(AnalysisResult.completed_at.desc()).first()
            
            if not latest_analysis:
                return {"status": "failed", "error": "No analysis results found. Run analysis first."}
            
            # Get materials and sections
            materials = {m.id: m for m in self.model.material_manager.get_all_materials()}
            sections = {s.id: s for s in self.model.section_manager.get_all_sections()}
            
            # Design each element
            design_results = []
            element_forces = latest_analysis.element_forces
            
            for element in elements:
                material = materials[element.material_id]
                section = sections[element.section_id]
                
                # Get element forces from analysis
                forces = element_forces.get(str(element.id), {})
                if not forces:
                    logging.warning(f"No forces found for element {element.id}")
                    continue
                
                # Extract forces
                max_moment_y = forces.get("max_moment_y", 0)
                max_moment_z = forces.get("max_moment_z", 0)
                max_shear_y = forces.get("max_shear_y", 0)
                max_shear_z = forces.get("max_shear_z", 0)
                max_axial = forces.get("max_axial", 0)
                
                # Design based on element type
                if element.element_type in ["beam"]:
                    # Beam design
                    flexure_result = self.rc_designer.design_beam_flexure(
                        element, material, section, max_moment_y, max_shear_y
                    )
                    shear_result = self.rc_designer.design_beam_shear(
                        element, material, section, max_shear_y, flexure_result["ast_provided"]
                    )
                    
                    # Combine results
                    element_result = {
                        "element_id": element.id,
                        "element_label": element.label,
                        "element_type": element.element_type,
                        "design_type": "beam",
                        "flexure": flexure_result,
                        "shear": shear_result,
                        "utilization_ratio": max(flexure_result["utilization_ratio"], 
                                               shear_result["utilization_ratio"]),
                        "design_passed": flexure_result["design_passed"] and shear_result["design_passed"]
                    }
                
                elif element.element_type in ["column"]:
                    # Column design
                    column_result = self.rc_designer.design_column(
                        element, material, section, max_axial, max_moment_y, max_moment_z
                    )
                    
                    element_result = {
                        "element_id": element.id,
                        "element_label": element.label,
                        "element_type": element.element_type,
                        "design_type": "column",
                        "column": column_result,
                        "utilization_ratio": column_result["utilization_ratio"],
                        "design_passed": column_result["design_passed"]
                    }
                
                else:
                    # Skip unsupported element types
                    continue
                
                design_results.append(element_result)
                
                # Store in database
                design_record = DesignResult(
                    model_id=self.model.model.id,
                    element_id=element.id,
                    design_code=design_code,
                    design_type=element_result["design_type"],
                    utilization_ratio=element_result["utilization_ratio"],
                    design_passed=element_result["design_passed"],
                    design_data=element_result,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(design_record)
            
            self.db.commit()
            
            # Generate summary
            summary = self.rc_designer.generate_design_summary(design_results)
            
            complete_results = {
                "status": "completed",
                "design_type": "rc_design",
                "design_code": design_code,
                "elements_designed": len(design_results),
                "design_results": design_results,
                "summary": summary
            }
            
            self.design_results["rc_design"] = complete_results
            logging.info(f"RC design completed for {len(design_results)} elements")
            
            return complete_results
            
        except Exception as e:
            logging.error(f"RC design failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def run_steel_design(self, design_code: str = "IS800", element_ids: List[int] = None) -> Dict[str, Any]:
        """Run steel design"""
        
        try:
            # Initialize steel designer
            self.steel_designer = SteelDesigner(design_code)
            
            # Get elements to design
            if element_ids:
                elements = [self.model.element_manager.get_element(eid) for eid in element_ids]
                elements = [e for e in elements if e is not None]
            else:
                # Get all steel elements
                all_elements = self.model.element_manager.get_all_elements()
                materials = {m.id: m for m in self.model.material_manager.get_all_materials()}
                elements = [e for e in all_elements if materials[e.material_id].material_type == "steel"]
            
            if not elements:
                return {"status": "failed", "error": "No steel elements found for design"}
            
            # Get latest analysis results
            from db.models import AnalysisResult
            latest_analysis = self.db.query(AnalysisResult).filter(
                AnalysisResult.model_id == self.model.model.id,
                AnalysisResult.analysis_type == "linear_static",
                AnalysisResult.status == "completed"
            ).order_by(AnalysisResult.completed_at.desc()).first()
            
            if not latest_analysis:
                return {"status": "failed", "error": "No analysis results found. Run analysis first."}
            
            # Get materials and sections
            materials = {m.id: m for m in self.model.material_manager.get_all_materials()}
            sections = {s.id: s for s in self.model.section_manager.get_all_sections()}
            
            # Design each element
            design_results = []
            element_forces = latest_analysis.element_forces
            
            for element in elements:
                material = materials[element.material_id]
                section = sections[element.section_id]
                
                # Get element forces from analysis
                forces = element_forces.get(str(element.id), {})
                if not forces:
                    logging.warning(f"No forces found for element {element.id}")
                    continue
                
                # Extract forces
                max_moment_y = forces.get("max_moment_y", 0)
                max_moment_z = forces.get("max_moment_z", 0)
                max_shear_y = forces.get("max_shear_y", 0)
                max_axial = forces.get("max_axial", 0)
                
                # Design based on element type and forces
                if element.element_type in ["beam"] or (abs(max_moment_y) > abs(max_axial) * 0.1):
                    # Beam design (flexure governs)
                    flexure_result = self.steel_designer.design_beam_flexure(
                        element, material, section, max_moment_y, max_shear_y
                    )
                    shear_result = self.steel_designer.design_beam_shear(
                        element, material, section, max_shear_y
                    )
                    
                    element_result = {
                        "element_id": element.id,
                        "element_label": element.label,
                        "element_type": element.element_type,
                        "design_type": "beam",
                        "flexure": flexure_result,
                        "shear": shear_result,
                        "utilization_ratio": max(flexure_result["utilization_ratio"], 
                                               shear_result["utilization_ratio"]),
                        "design_passed": flexure_result["design_passed"] and shear_result["design_passed"]
                    }
                
                elif element.element_type in ["column"] or abs(max_axial) > 0:
                    # Column design (compression + bending)
                    column_result = self.steel_designer.design_column(
                        element, material, section, max_axial, max_moment_y, max_moment_z
                    )
                    
                    element_result = {
                        "element_id": element.id,
                        "element_label": element.label,
                        "element_type": element.element_type,
                        "design_type": "column",
                        "column": column_result,
                        "utilization_ratio": column_result["utilization_ratio"],
                        "design_passed": column_result["design_passed"]
                    }
                
                elif element.element_type in ["brace"] or max_axial < 0:
                    # Tension member design
                    tension_result = self.steel_designer.design_tension_member(
                        element, material, section, abs(max_axial)
                    )
                    
                    element_result = {
                        "element_id": element.id,
                        "element_label": element.label,
                        "element_type": element.element_type,
                        "design_type": "tension",
                        "tension": tension_result,
                        "utilization_ratio": tension_result["utilization_ratio"],
                        "design_passed": tension_result["design_passed"]
                    }
                
                else:
                    # Default to compression member
                    column_result = self.steel_designer.design_column(
                        element, material, section, max_axial, max_moment_y, max_moment_z
                    )
                    
                    element_result = {
                        "element_id": element.id,
                        "element_label": element.label,
                        "element_type": element.element_type,
                        "design_type": "compression",
                        "column": column_result,
                        "utilization_ratio": column_result["utilization_ratio"],
                        "design_passed": column_result["design_passed"]
                    }
                
                design_results.append(element_result)
                
                # Store in database
                design_record = DesignResult(
                    model_id=self.model.model.id,
                    element_id=element.id,
                    design_code=design_code,
                    design_type=element_result["design_type"],
                    utilization_ratio=element_result["utilization_ratio"],
                    design_passed=element_result["design_passed"],
                    design_data=element_result,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(design_record)
            
            self.db.commit()
            
            # Generate summary
            summary = self.steel_designer.generate_design_summary(design_results)
            
            complete_results = {
                "status": "completed",
                "design_type": "steel_design",
                "design_code": design_code,
                "elements_designed": len(design_results),
                "design_results": design_results,
                "summary": summary
            }
            
            self.design_results["steel_design"] = complete_results
            logging.info(f"Steel design completed for {len(design_results)} elements")
            
            return complete_results
            
        except Exception as e:
            logging.error(f"Steel design failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def get_design_summary(self) -> Dict[str, Any]:
        """Get summary of all completed designs"""
        
        # Get completed designs from database
        completed_designs = self.db.query(DesignResult).filter(
            DesignResult.model_id == self.model.model.id
        ).all()
        
        summary = {
            "model_id": self.model.model.id,
            "total_designs": len(completed_designs),
            "design_types": [],
            "design_codes": [],
            "passed_elements": 0,
            "failed_elements": 0,
            "max_utilization": 0,
            "critical_elements": []
        }
        
        for design in completed_designs:
            if design.design_type not in summary["design_types"]:
                summary["design_types"].append(design.design_type)
            
            if design.design_code not in summary["design_codes"]:
                summary["design_codes"].append(design.design_code)
            
            if design.design_passed:
                summary["passed_elements"] += 1
            else:
                summary["failed_elements"] += 1
            
            if design.utilization_ratio > summary["max_utilization"]:
                summary["max_utilization"] = design.utilization_ratio
            
            if design.utilization_ratio > 0.9:
                summary["critical_elements"].append({
                    "element_id": design.element_id,
                    "design_type": design.design_type,
                    "utilization_ratio": design.utilization_ratio,
                    "design_passed": design.design_passed
                })
        
        if summary["total_designs"] > 0:
            summary["pass_percentage"] = (summary["passed_elements"] / summary["total_designs"]) * 100
        else:
            summary["pass_percentage"] = 0
        
        return summary
    
    def get_element_design_results(self, element_id: int) -> Optional[Dict]:
        """Get design results for specific element"""
        
        design_result = self.db.query(DesignResult).filter(
            DesignResult.model_id == self.model.model.id,
            DesignResult.element_id == element_id
        ).order_by(DesignResult.created_at.desc()).first()
        
        if design_result:
            return {
                "element_id": design_result.element_id,
                "design_type": design_result.design_type,
                "design_code": design_result.design_code,
                "utilization_ratio": design_result.utilization_ratio,
                "design_passed": design_result.design_passed,
                "design_data": design_result.design_data,
                "created_at": design_result.created_at
            }
        
        return None
    
    def clear_design_results(self):
        """Clear all design results"""
        
        # Clear from database
        self.db.query(DesignResult).filter(
            DesignResult.model_id == self.model.model.id
        ).delete()
        self.db.commit()
        
        # Clear from memory
        self.design_results.clear()
        
        logging.info("All design results cleared")
    
    def export_design_results(self, design_type: str = None) -> Dict[str, Any]:
        """Export design results for external use"""
        
        if design_type and design_type in self.design_results:
            return self.design_results[design_type]
        
        return self.design_results
