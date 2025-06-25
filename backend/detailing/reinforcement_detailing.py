import math
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from backend.db.models import Element, Material, Section, ReinforcementDetail


class ReinforcementDetailer:
    """Reinforcement detailing generator for RC elements"""
    
    def __init__(self, design_code: str = "IS456"):
        self.design_code = design_code
        self.rebar_grades = self._get_rebar_grades()
        self.standard_diameters = [6, 8, 10, 12, 16, 20, 25, 32, 36, 40]  # mm
    
    def _get_rebar_grades(self) -> Dict:
        """Get standard rebar grades and properties"""
        return {
            "Fe415": {"fy": 415, "density": 7850},  # kg/m³
            "Fe500": {"fy": 500, "density": 7850},
            "Fe550": {"fy": 550, "density": 7850},
            "Fe600": {"fy": 600, "density": 7850}
        }
    
    def detail_beam_reinforcement(self, element: Element, design_result: Dict, 
                                cover: float = 25) -> Dict[str, Any]:
        """Generate detailed reinforcement for RC beam"""
        
        # Extract design data
        flexure_data = design_result.get("flexure", {})
        shear_data = design_result.get("shear", {})
        
        ast_required = flexure_data.get("ast_required", 0)
        asc_required = flexure_data.get("asc_required", 0)
        
        # Get section dimensions
        section_dims = design_result.get("flexure", {}).get("design_details", {})
        b = section_dims.get("b", 300)  # mm
        h = section_dims.get("h", 450)  # mm
        d = section_dims.get("d", h - cover - 10)  # effective depth
        
        # Select rebar sizes and layout
        main_rebar = self._select_main_reinforcement(ast_required, b, d)
        compression_rebar = self._select_compression_reinforcement(asc_required, b) if asc_required > 0 else None
        
        # Stirrup design
        stirrup_details = self._design_stirrups(shear_data, b, h)
        
        # Calculate development lengths
        main_rebar_dia = main_rebar["diameter"]
        development_length = self._calculate_development_length(main_rebar_dia, design_result)
        
        # Generate bar schedule
        bar_schedule = self._generate_bar_schedule(element, main_rebar, compression_rebar, stirrup_details)
        
        # Calculate quantities
        concrete_volume = self._calculate_concrete_volume(element, b, h)
        steel_weight = self._calculate_steel_weight(bar_schedule)
        
        return {
            "element_id": element.id,
            "element_type": "beam",
            "section_dimensions": {"b": b, "h": h, "d": d},
            "cover": cover,
            "main_reinforcement": main_rebar,
            "compression_reinforcement": compression_rebar,
            "stirrups": stirrup_details,
            "development_length": development_length,
            "bar_schedule": bar_schedule,
            "quantities": {
                "concrete_volume": concrete_volume,
                "steel_weight": steel_weight,
                "formwork_area": self._calculate_formwork_area(element, b, h)
            },
            "drawings": self._generate_beam_drawing_data(main_rebar, compression_rebar, stirrup_details, b, h, cover)
        }
    
    def detail_column_reinforcement(self, element: Element, design_result: Dict,
                                  cover: float = 40) -> Dict[str, Any]:
        """Generate detailed reinforcement for RC column"""
        
        # Extract design data
        column_data = design_result.get("column", {})
        ast_required = column_data.get("ast_required", 0)
        
        # Get section dimensions
        section_dims = design_result.get("column", {}).get("design_details", {}) or {"b": 300, "h": 300}
        b = section_dims.get("b", 300)  # mm
        h = section_dims.get("h", 300)  # mm
        
        # Select longitudinal reinforcement
        long_rebar = self._select_column_longitudinal_reinforcement(ast_required, b, h)
        
        # Design ties/spirals
        tie_details = self._design_column_ties(long_rebar, b, h)
        
        # Calculate development lengths
        main_rebar_dia = long_rebar["diameter"]
        development_length = self._calculate_development_length(main_rebar_dia, design_result)
        
        # Generate bar schedule
        bar_schedule = self._generate_column_bar_schedule(element, long_rebar, tie_details)
        
        # Calculate quantities
        concrete_volume = self._calculate_concrete_volume(element, b, h)
        steel_weight = self._calculate_steel_weight(bar_schedule)
        
        return {
            "element_id": element.id,
            "element_type": "column",
            "section_dimensions": {"b": b, "h": h},
            "cover": cover,
            "longitudinal_reinforcement": long_rebar,
            "ties": tie_details,
            "development_length": development_length,
            "bar_schedule": bar_schedule,
            "quantities": {
                "concrete_volume": concrete_volume,
                "steel_weight": steel_weight,
                "formwork_area": self._calculate_formwork_area(element, b, h)
            },
            "drawings": self._generate_column_drawing_data(long_rebar, tie_details, b, h, cover)
        }
    
    def _select_main_reinforcement(self, ast_required: float, width: float, 
                                 effective_depth: float) -> Dict[str, Any]:
        """Select main reinforcement bars for beam"""
        
        # Try different bar sizes starting from larger ones
        for dia in reversed(self.standard_diameters):
            if dia < 12:  # Minimum 12mm for main bars
                continue
            
            bar_area = math.pi * (dia/2)**2
            num_bars_required = math.ceil(ast_required / bar_area)
            
            # Check if bars fit in the width
            clear_cover = 25
            stirrup_dia = 8
            available_width = width - 2 * (clear_cover + stirrup_dia)
            min_spacing = max(dia, 25)  # Minimum spacing between bars
            
            required_width = num_bars_required * dia + (num_bars_required - 1) * min_spacing
            
            if required_width <= available_width and num_bars_required <= 6:
                # Check for practical limits
                actual_spacing = (available_width - num_bars_required * dia) / (num_bars_required - 1) if num_bars_required > 1 else 0
                
                return {
                    "diameter": dia,
                    "number_of_bars": num_bars_required,
                    "area_provided": num_bars_required * bar_area,
                    "area_required": ast_required,
                    "spacing": actual_spacing,
                    "grade": "Fe415",
                    "arrangement": self._get_bar_arrangement(num_bars_required, width)
                }
        
        # If no single size works, use combination
        return self._select_combination_reinforcement(ast_required, width)
    
    def _select_compression_reinforcement(self, asc_required: float, width: float) -> Dict[str, Any]:
        """Select compression reinforcement"""
        
        if asc_required <= 0:
            return None
        
        # Usually same size as tension reinforcement but fewer bars
        for dia in [20, 16, 12]:
            bar_area = math.pi * (dia/2)**2
            num_bars_required = math.ceil(asc_required / bar_area)
            
            if num_bars_required <= 4:  # Practical limit for compression bars
                return {
                    "diameter": dia,
                    "number_of_bars": num_bars_required,
                    "area_provided": num_bars_required * bar_area,
                    "area_required": asc_required,
                    "grade": "Fe415"
                }
        
        return {
            "diameter": 12,
            "number_of_bars": 2,
            "area_provided": 2 * math.pi * 6**2,
            "area_required": asc_required,
            "grade": "Fe415"
        }
    
    def _select_combination_reinforcement(self, ast_required: float, width: float) -> Dict[str, Any]:
        """Select combination of bar sizes if single size doesn't work"""
        
        # Use combination of 20mm and 16mm bars
        dia1, dia2 = 20, 16
        area1 = math.pi * (dia1/2)**2
        area2 = math.pi * (dia2/2)**2
        
        # Try different combinations
        for n1 in range(1, 5):  # Number of larger bars
            for n2 in range(1, 5):  # Number of smaller bars
                total_area = n1 * area1 + n2 * area2
                
                if total_area >= ast_required:
                    # Check if they fit
                    available_width = width - 2 * (25 + 8)  # cover + stirrup
                    total_bars = n1 + n2
                    min_spacing = 25
                    required_width = total_bars * 20 + (total_bars - 1) * min_spacing  # Use larger dia for spacing
                    
                    if required_width <= available_width:
                        return {
                            "diameter": [dia1, dia2],
                            "number_of_bars": [n1, n2],
                            "area_provided": total_area,
                            "area_required": ast_required,
                            "grade": "Fe415",
                            "type": "combination"
                        }
        
        # Fallback to minimum practical arrangement
        return {
            "diameter": 12,
            "number_of_bars": max(2, math.ceil(ast_required / (math.pi * 6**2))),
            "area_provided": max(2, math.ceil(ast_required / (math.pi * 6**2))) * math.pi * 6**2,
            "area_required": ast_required,
            "grade": "Fe415"
        }
    
    def _design_stirrups(self, shear_data: Dict, width: float, height: float) -> Dict[str, Any]:
        """Design stirrup reinforcement"""
        
        stirrup_diameter = shear_data.get("stirrup_diameter", 8)
        stirrup_spacing = shear_data.get("stirrup_spacing", 200)
        
        if stirrup_spacing == "Not required":
            stirrup_spacing = min(0.75 * (height - 50), 300)  # Maximum spacing
        
        # Ensure practical limits
        stirrup_spacing = max(min(stirrup_spacing, 300), 75)  # Between 75mm and 300mm
        
        # Calculate stirrup length
        clear_cover = 25
        hook_length = 10 * stirrup_diameter  # Hook development length
        stirrup_length = 2 * (width - 2 * clear_cover) + 2 * (height - 2 * clear_cover) + 2 * hook_length
        
        return {
            "diameter": stirrup_diameter,
            "spacing": stirrup_spacing,
            "legs": 2,
            "length_per_stirrup": stirrup_length,
            "hook_type": "135_degree",
            "grade": "Fe415"
        }
    
    def _select_column_longitudinal_reinforcement(self, ast_required: float, 
                                                width: float, height: float) -> Dict[str, Any]:
        """Select longitudinal reinforcement for column"""
        
        # Minimum bars based on column size
        if width <= 250:
            min_bars = 4
        elif width <= 350:
            min_bars = 6
        else:
            min_bars = 8
        
        # Try different bar sizes
        for dia in [25, 20, 16, 12]:
            bar_area = math.pi * (dia/2)**2
            num_bars_required = max(min_bars, math.ceil(ast_required / bar_area))
            
            # Check if bars fit around perimeter
            perimeter = 2 * (width + height) - 4 * 40  # Account for corner bars and cover
            spacing_required = perimeter / num_bars_required
            
            if spacing_required >= max(dia, 75):  # Minimum spacing
                return {
                    "diameter": dia,
                    "number_of_bars": num_bars_required,
                    "area_provided": num_bars_required * bar_area,
                    "area_required": ast_required,
                    "spacing": spacing_required,
                    "grade": "Fe415",
                    "arrangement": self._get_column_bar_arrangement(num_bars_required, width, height)
                }
        
        # Fallback
        return {
            "diameter": 16,
            "number_of_bars": max(min_bars, 8),
            "area_provided": max(min_bars, 8) * math.pi * 8**2,
            "area_required": ast_required,
            "grade": "Fe415"
        }
    
    def _design_column_ties(self, longitudinal_rebar: Dict, width: float, height: float) -> Dict[str, Any]:
        """Design column ties/lateral reinforcement"""
        
        main_bar_dia = longitudinal_rebar["diameter"]
        
        # Tie diameter (minimum 6mm, quarter of main bar diameter)
        tie_dia = max(6, main_bar_dia // 4)
        tie_dia = min(tie_dia, 12)  # Maximum 12mm
        
        # Tie spacing
        if self.design_code == "IS456":
            spacing = min(
                16 * main_bar_dia,  # 16 times main bar diameter
                min(width, height),   # Least lateral dimension
                300                   # 300mm maximum
            )
        else:
            spacing = min(16 * main_bar_dia, min(width, height), 400)
        
        # Calculate tie length
        clear_cover = 40
        hook_length = 10 * tie_dia
        tie_length = 2 * (width - 2 * clear_cover) + 2 * (height - 2 * clear_cover) + 2 * hook_length
        
        return {
            "diameter": tie_dia,
            "spacing": spacing,
            "length_per_tie": tie_length,
            "hook_type": "135_degree",
            "grade": "Fe415"
        }
    
    def _calculate_development_length(self, bar_diameter: float, design_result: Dict) -> float:
        """Calculate development length for reinforcement"""
        
        # Get material properties
        design_details = design_result.get("flexure", {}).get("design_details", {})
        fck = design_details.get("fck", 25)
        fy = design_details.get("fy", 415)
        
        if self.design_code == "IS456":
            # IS 456 development length
            tau_bd = 1.2 * math.sqrt(fck)  # Design bond stress
            ld = fy * bar_diameter / (4 * tau_bd)
        else:
            # Simplified calculation
            ld = fy * bar_diameter / (4 * 1.2 * math.sqrt(fck))
        
        return max(ld, 200)  # Minimum 200mm
    
    def _generate_bar_schedule(self, element: Element, main_rebar: Dict, 
                             compression_rebar: Dict, stirrup_details: Dict) -> List[Dict]:
        """Generate bar bending schedule"""
        
        element_length = 3000  # Simplified - would calculate from geometry
        
        schedule = []
        
        # Main reinforcement
        main_bars = main_rebar["number_of_bars"]
        main_dia = main_rebar["diameter"]
        main_length = element_length + 2 * self._calculate_development_length(main_dia, {})
        
        schedule.append({
            "bar_mark": "M1",
            "diameter": main_dia,
            "number": main_bars,
            "length": main_length,
            "shape": "straight",
            "total_length": main_bars * main_length,
            "weight": main_bars * main_length * (main_dia**2 * math.pi / 4) * 7.85e-6,  # kg
            "description": "Main tension reinforcement"
        })
        
        # Compression reinforcement
        if compression_rebar:
            comp_bars = compression_rebar["number_of_bars"]
            comp_dia = compression_rebar["diameter"]
            comp_length = element_length
            
            schedule.append({
                "bar_mark": "C1",
                "diameter": comp_dia,
                "number": comp_bars,
                "length": comp_length,
                "shape": "straight",
                "total_length": comp_bars * comp_length,
                "weight": comp_bars * comp_length * (comp_dia**2 * math.pi / 4) * 7.85e-6,
                "description": "Compression reinforcement"
            })
        
        # Stirrups
        stirrup_dia = stirrup_details["diameter"]
        stirrup_spacing = stirrup_details["spacing"]
        stirrup_length = stirrup_details["length_per_stirrup"]
        num_stirrups = math.ceil(element_length / stirrup_spacing) + 1
        
        schedule.append({
            "bar_mark": "S1",
            "diameter": stirrup_dia,
            "number": num_stirrups,
            "length": stirrup_length,
            "shape": "rectangular_stirrup",
            "total_length": num_stirrups * stirrup_length,
            "weight": num_stirrups * stirrup_length * (stirrup_dia**2 * math.pi / 4) * 7.85e-6,
            "description": f"Stirrups @ {stirrup_spacing}mm c/c"
        })
        
        return schedule
    
    def _generate_column_bar_schedule(self, element: Element, longitudinal_rebar: Dict,
                                    tie_details: Dict) -> List[Dict]:
        """Generate bar schedule for column"""
        
        element_length = 3000  # Simplified
        
        schedule = []
        
        # Longitudinal bars
        long_bars = longitudinal_rebar["number_of_bars"]
        long_dia = longitudinal_rebar["diameter"]
        long_length = element_length + 750  # Lap length
        
        schedule.append({
            "bar_mark": "L1",
            "diameter": long_dia,
            "number": long_bars,
            "length": long_length,
            "shape": "straight",
            "total_length": long_bars * long_length,
            "weight": long_bars * long_length * (long_dia**2 * math.pi / 4) * 7.85e-6,
            "description": "Longitudinal reinforcement"
        })
        
        # Ties
        tie_dia = tie_details["diameter"]
        tie_spacing = tie_details["spacing"]
        tie_length = tie_details["length_per_tie"]
        num_ties = math.ceil(element_length / tie_spacing) + 1
        
        schedule.append({
            "bar_mark": "T1",
            "diameter": tie_dia,
            "number": num_ties,
            "length": tie_length,
            "shape": "rectangular_tie",
            "total_length": num_ties * tie_length,
            "weight": num_ties * tie_length * (tie_dia**2 * math.pi / 4) * 7.85e-6,
            "description": f"Ties @ {tie_spacing}mm c/c"
        })
        
        return schedule
    
    def _calculate_concrete_volume(self, element: Element, width: float, height: float) -> float:
        """Calculate concrete volume in cubic meters"""
        length = 3.0  # Simplified
        return (width * height * length) / 1e9  # Convert mm³ to m³
    
    def _calculate_steel_weight(self, bar_schedule: List[Dict]) -> float:
        """Calculate total steel weight in kg"""
        return sum(item["weight"] for item in bar_schedule)
    
    def _calculate_formwork_area(self, element: Element, width: float, height: float) -> float:
        """Calculate formwork area in square meters"""
        length = 3.0  # Simplified
        # Bottom + 2 sides for beam, all 4 sides for column
        if hasattr(element, 'element_type') and element.element_type == "beam":
            return (width + 2 * height) * length / 1e6  # Convert mm² to m²
        else:
            return 2 * (width + height) * length / 1e6
    
    def _get_bar_arrangement(self, num_bars: int, width: float) -> str:
        """Get textual description of bar arrangement"""
        if num_bars <= 2:
            return f"{num_bars} bars in single layer"
        elif num_bars <= 4:
            return f"{num_bars} bars in single layer"
        else:
            return f"{num_bars} bars in two layers"
    
    def _get_column_bar_arrangement(self, num_bars: int, width: float, height: float) -> str:
        """Get column bar arrangement description"""
        if num_bars == 4:
            return "4 bars at corners"
        elif num_bars == 6:
            return "6 bars - 4 corners + 2 face centers"
        elif num_bars == 8:
            return "8 bars around perimeter"
        else:
            return f"{num_bars} bars distributed around perimeter"
    
    def _generate_beam_drawing_data(self, main_rebar: Dict, compression_rebar: Dict,
                                  stirrup_details: Dict, width: float, height: float,
                                  cover: float) -> Dict[str, Any]:
        """Generate drawing data for beam detailing"""
        
        return {
            "section_view": {
                "width": width,
                "height": height,
                "cover": cover,
                "main_bars": {
                    "diameter": main_rebar["diameter"],
                    "count": main_rebar["number_of_bars"],
                    "position": "bottom"
                },
                "compression_bars": compression_rebar if compression_rebar else None,
                "stirrups": {
                    "diameter": stirrup_details["diameter"],
                    "spacing": stirrup_details["spacing"]
                }
            },
            "elevation_view": {
                "stirrup_spacing": stirrup_details["spacing"],
                "development_lengths": True
            }
        }
    
    def _generate_column_drawing_data(self, longitudinal_rebar: Dict, tie_details: Dict,
                                    width: float, height: float, cover: float) -> Dict[str, Any]:
        """Generate drawing data for column detailing"""
        
        return {
            "section_view": {
                "width": width,
                "height": height,
                "cover": cover,
                "longitudinal_bars": {
                    "diameter": longitudinal_rebar["diameter"],
                    "count": longitudinal_rebar["number_of_bars"],
                    "arrangement": longitudinal_rebar.get("arrangement", "")
                },
                "ties": {
                    "diameter": tie_details["diameter"],
                    "spacing": tie_details["spacing"]
                }
            },
            "elevation_view": {
                "tie_spacing": tie_details["spacing"],
                "lap_splices": True
            }
        }
