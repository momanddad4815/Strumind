from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from core.model import StructuralModel
from detailing.reinforcement_detailing import ReinforcementDetailer
from db.models import ReinforcementDetail, ConnectionDetail, DesignResult
import logging
from datetime import datetime


class DetailingEngine:
    """Main detailing engine that coordinates reinforcement and steel detailing"""
    
    def __init__(self, structural_model: StructuralModel):
        self.model = structural_model
        self.db = structural_model.db
        
        # Detailing components
        self.reinforcement_detailer = None
        
        # Results storage
        self.detailing_results = {}
    
    def generate_reinforcement_details(self, design_code: str = "IS456", 
                                     element_ids: List[int] = None) -> Dict[str, Any]:
        """Generate reinforcement details for RC elements"""
        
        try:
            # Initialize reinforcement detailer
            self.reinforcement_detailer = ReinforcementDetailer(design_code)
            
            # Get elements to detail
            if element_ids:
                elements = [self.model.element_manager.get_element(eid) for eid in element_ids]
                elements = [e for e in elements if e is not None]
            else:
                # Get all concrete elements that have been designed
                designed_elements = self.db.query(DesignResult).filter(
                    DesignResult.model_id == self.model.model.id,
                    DesignResult.design_passed == True
                ).all()
                
                element_ids_designed = [dr.element_id for dr in designed_elements]
                elements = [self.model.element_manager.get_element(eid) for eid in element_ids_designed]
                elements = [e for e in elements if e is not None]
            
            if not elements:
                return {"status": "failed", "error": "No designed concrete elements found for detailing"}
            
            # Get design results
            design_results = {}
            for element in elements:
                design_result = self.db.query(DesignResult).filter(
                    DesignResult.model_id == self.model.model.id,
                    DesignResult.element_id == element.id
                ).order_by(DesignResult.created_at.desc()).first()
                
                if design_result:
                    design_results[element.id] = design_result.design_data
            
            # Detail each element
            detailing_results = []
            
            for element in elements:
                if element.id not in design_results:
                    logging.warning(f"No design results found for element {element.id}")
                    continue
                
                design_data = design_results[element.id]
                
                # Generate reinforcement details based on element type
                if element.element_type in ["beam"]:
                    detail_result = self.reinforcement_detailer.detail_beam_reinforcement(
                        element, design_data
                    )
                elif element.element_type in ["column"]:
                    detail_result = self.reinforcement_detailer.detail_column_reinforcement(
                        element, design_data
                    )
                else:
                    logging.warning(f"Element type {element.element_type} not supported for detailing")
                    continue
                
                detailing_results.append(detail_result)
                
                # Store in database
                rebar_detail = ReinforcementDetail(
                    model_id=self.model.model.id,
                    element_id=element.id,
                    top_rebar_size=str(detail_result.get("compression_reinforcement", {}).get("diameter", "")),
                    top_rebar_count=detail_result.get("compression_reinforcement", {}).get("number_of_bars", 0),
                    bottom_rebar_size=str(detail_result.get("main_reinforcement", {}).get("diameter", "")),
                    bottom_rebar_count=detail_result.get("main_reinforcement", {}).get("number_of_bars", 0),
                    stirrup_size=str(detail_result.get("stirrups", {}).get("diameter", detail_result.get("ties", {}).get("diameter", ""))),
                    stirrup_spacing=detail_result.get("stirrups", {}).get("spacing", detail_result.get("ties", {}).get("spacing", 0)),
                    stirrup_legs=detail_result.get("stirrups", {}).get("legs", 2),
                    cover=detail_result.get("cover", 25),
                    development_length=detail_result.get("development_length", 0),
                    bar_schedule=detail_result.get("bar_schedule", [])
                )
                
                self.db.add(rebar_detail)
            
            self.db.commit()
            
            # Calculate summary quantities
            summary = self._calculate_detailing_summary(detailing_results)
            
            complete_results = {
                "status": "completed",
                "detailing_type": "reinforcement",
                "design_code": design_code,
                "elements_detailed": len(detailing_results),
                "detailing_results": detailing_results,
                "summary": summary
            }
            
            self.detailing_results["reinforcement"] = complete_results
            logging.info(f"Reinforcement detailing completed for {len(detailing_results)} elements")
            
            return complete_results
            
        except Exception as e:
            logging.error(f"Reinforcement detailing failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def generate_bar_bending_schedule(self, element_ids: List[int] = None) -> Dict[str, Any]:
        """Generate comprehensive bar bending schedule"""
        
        try:
            # Get reinforcement details
            if element_ids:
                rebar_details = self.db.query(ReinforcementDetail).filter(
                    ReinforcementDetail.model_id == self.model.model.id,
                    ReinforcementDetail.element_id.in_(element_ids)
                ).all()
            else:
                rebar_details = self.db.query(ReinforcementDetail).filter(
                    ReinforcementDetail.model_id == self.model.model.id
                ).all()
            
            if not rebar_details:
                return {"status": "failed", "error": "No reinforcement details found"}
            
            # Consolidate bar schedule
            consolidated_schedule = {}
            total_steel_weight = 0
            
            for detail in rebar_details:
                element = self.model.element_manager.get_element(detail.element_id)
                
                # Process bar schedule for this element
                bar_schedule = detail.bar_schedule or []
                
                for bar_item in bar_schedule:
                    bar_mark = bar_item.get("bar_mark", "")
                    diameter = bar_item.get("diameter", 0)
                    shape = bar_item.get("shape", "straight")
                    length = bar_item.get("length", 0)
                    
                    # Create unique key for similar bars
                    key = f"{diameter}mm_{shape}_{length}mm"
                    
                    if key not in consolidated_schedule:
                        consolidated_schedule[key] = {
                            "diameter": diameter,
                            "shape": shape,
                            "length": length,
                            "total_number": 0,
                            "total_length": 0,
                            "total_weight": 0,
                            "elements": []
                        }
                    
                    # Add to consolidated schedule
                    consolidated_schedule[key]["total_number"] += bar_item.get("number", 0)
                    consolidated_schedule[key]["total_length"] += bar_item.get("total_length", 0)
                    consolidated_schedule[key]["total_weight"] += bar_item.get("weight", 0)
                    consolidated_schedule[key]["elements"].append({
                        "element_id": element.id,
                        "element_label": element.label,
                        "number": bar_item.get("number", 0)
                    })
                    
                    total_steel_weight += bar_item.get("weight", 0)
            
            # Convert to list and sort by diameter
            schedule_list = list(consolidated_schedule.values())
            schedule_list.sort(key=lambda x: x["diameter"], reverse=True)
            
            # Calculate steel quantities by diameter
            steel_summary = {}
            for item in schedule_list:
                dia = item["diameter"]
                if dia not in steel_summary:
                    steel_summary[dia] = {
                        "diameter": dia,
                        "total_length": 0,
                        "total_weight": 0,
                        "number_of_pieces": 0
                    }
                
                steel_summary[dia]["total_length"] += item["total_length"]
                steel_summary[dia]["total_weight"] += item["total_weight"]
                steel_summary[dia]["number_of_pieces"] += item["total_number"]
            
            return {
                "status": "completed",
                "model_id": self.model.model.id,
                "total_elements": len(rebar_details),
                "bar_bending_schedule": schedule_list,
                "steel_summary": list(steel_summary.values()),
                "total_steel_weight": total_steel_weight,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logging.error(f"Bar bending schedule generation failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def generate_quantity_takeoff(self) -> Dict[str, Any]:
        """Generate quantity takeoff for the entire model"""
        
        try:
            # Get all reinforcement details
            rebar_details = self.db.query(ReinforcementDetail).filter(
                ReinforcementDetail.model_id == self.model.model.id
            ).all()
            
            # Initialize quantities
            quantities = {
                "concrete": {"volume": 0, "unit": "m³"},
                "steel": {"weight": 0, "unit": "kg"},
                "formwork": {"area": 0, "unit": "m²"}
            }
            
            element_quantities = []
            
            # Get detailing results for quantities
            if "reinforcement" in self.detailing_results:
                detailing_data = self.detailing_results["reinforcement"]["detailing_results"]
                
                for element_detail in detailing_data:
                    element_qty = element_detail.get("quantities", {})
                    
                    # Add to totals
                    quantities["concrete"]["volume"] += element_qty.get("concrete_volume", 0)
                    quantities["steel"]["weight"] += element_qty.get("steel_weight", 0)
                    quantities["formwork"]["area"] += element_qty.get("formwork_area", 0)
                    
                    # Store element-wise quantities
                    element_quantities.append({
                        "element_id": element_detail["element_id"],
                        "element_type": element_detail["element_type"],
                        "concrete_volume": element_qty.get("concrete_volume", 0),
                        "steel_weight": element_qty.get("steel_weight", 0),
                        "formwork_area": element_qty.get("formwork_area", 0)
                    })
            
            # Calculate costs (example rates)
            rates = {
                "concrete": 5000,  # ₹/m³
                "steel": 60,       # ₹/kg
                "formwork": 300    # ₹/m²
            }
            
            costs = {
                "concrete": quantities["concrete"]["volume"] * rates["concrete"],
                "steel": quantities["steel"]["weight"] * rates["steel"],
                "formwork": quantities["formwork"]["area"] * rates["formwork"]
            }
            
            total_cost = sum(costs.values())
            
            return {
                "status": "completed",
                "model_id": self.model.model.id,
                "quantities": quantities,
                "element_quantities": element_quantities,
                "rates": rates,
                "costs": costs,
                "total_cost": total_cost,
                "currency": "INR",
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logging.error(f"Quantity takeoff generation failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def _calculate_detailing_summary(self, detailing_results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary of detailing results"""
        
        total_elements = len(detailing_results)
        total_concrete_volume = sum(dr.get("quantities", {}).get("concrete_volume", 0) for dr in detailing_results)
        total_steel_weight = sum(dr.get("quantities", {}).get("steel_weight", 0) for dr in detailing_results)
        total_formwork_area = sum(dr.get("quantities", {}).get("formwork_area", 0) for dr in detailing_results)
        
        # Count elements by type
        element_types = {}
        for dr in detailing_results:
            element_type = dr.get("element_type", "unknown")
            element_types[element_type] = element_types.get(element_type, 0) + 1
        
        # Calculate steel intensity
        steel_intensity = total_steel_weight / total_concrete_volume if total_concrete_volume > 0 else 0
        
        return {
            "total_elements_detailed": total_elements,
            "element_types": element_types,
            "total_concrete_volume": total_concrete_volume,
            "total_steel_weight": total_steel_weight,
            "total_formwork_area": total_formwork_area,
            "steel_intensity": steel_intensity,  # kg/m³
            "average_cover": 25,  # Simplified
            "design_code": self.reinforcement_detailer.design_code if self.reinforcement_detailer else "IS456"
        }
    
    def get_element_reinforcement_details(self, element_id: int) -> Optional[Dict]:
        """Get reinforcement details for specific element"""
        
        rebar_detail = self.db.query(ReinforcementDetail).filter(
            ReinforcementDetail.model_id == self.model.model.id,
            ReinforcementDetail.element_id == element_id
        ).first()
        
        if rebar_detail:
            return {
                "element_id": rebar_detail.element_id,
                "top_rebar_size": rebar_detail.top_rebar_size,
                "top_rebar_count": rebar_detail.top_rebar_count,
                "bottom_rebar_size": rebar_detail.bottom_rebar_size,
                "bottom_rebar_count": rebar_detail.bottom_rebar_count,
                "stirrup_size": rebar_detail.stirrup_size,
                "stirrup_spacing": rebar_detail.stirrup_spacing,
                "stirrup_legs": rebar_detail.stirrup_legs,
                "cover": rebar_detail.cover,
                "development_length": rebar_detail.development_length,
                "bar_schedule": rebar_detail.bar_schedule
            }
        
        return None
    
    def clear_detailing_results(self):
        """Clear all detailing results"""
        
        # Clear from database
        self.db.query(ReinforcementDetail).filter(
            ReinforcementDetail.model_id == self.model.model.id
        ).delete()
        
        self.db.query(ConnectionDetail).filter(
            ConnectionDetail.model_id == self.model.model.id
        ).delete()
        
        self.db.commit()
        
        # Clear from memory
        self.detailing_results.clear()
        
        logging.info("All detailing results cleared")
    
    def export_detailing_results(self, detailing_type: str = None) -> Dict[str, Any]:
        """Export detailing results for external use"""
        
        if detailing_type and detailing_type in self.detailing_results:
            return self.detailing_results[detailing_type]
        
        return self.detailing_results
