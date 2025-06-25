import math
from typing import Dict, List, Tuple, Optional
import numpy as np
from backend.db.models import Element, Material, Section, DesignResult


class RCDesigner:
    """Reinforced Concrete Design Engine supporting multiple international codes"""
    
    def __init__(self, design_code: str = "IS456"):
        self.design_code = design_code
        self.design_constants = self._get_design_constants()
    
    def _get_design_constants(self) -> Dict:
        """Get design constants based on code"""
        
        if self.design_code == "IS456":
            return {
                "gamma_c": 1.5,  # Partial safety factor for concrete
                "gamma_s": 1.15,  # Partial safety factor for steel
                "alpha": 0.85,   # Stress block factor
                "beta": 0.416,   # Neutral axis factor
                "k_max": 0.48,   # Maximum neutral axis depth ratio
                "tau_c_max": 4.0,  # Maximum concrete shear stress (N/mm²)
                "cover_min": 25,  # Minimum cover (mm)
            }
        
        elif self.design_code == "ACI318":
            return {
                "gamma_c": 0.65,  # Strength reduction factor for flexure
                "gamma_s": 0.9,   # Strength reduction factor for tension
                "alpha": 0.85,    # Stress block factor
                "beta": 0.85,     # Stress block factor
                "k_max": 0.42,    # Maximum neutral axis depth ratio
                "tau_c_max": 0.17,  # √f'c (psi units)
                "cover_min": 40,   # Minimum cover (mm)
            }
        
        elif self.design_code == "EC2":
            return {
                "gamma_c": 1.5,   # Partial safety factor for concrete
                "gamma_s": 1.15,  # Partial safety factor for steel
                "alpha": 0.85,    # Stress block factor
                "beta": 0.8,      # Neutral axis factor
                "k_max": 0.45,    # Maximum neutral axis depth ratio
                "tau_c_max": 0.25,  # Maximum concrete shear stress ratio
                "cover_min": 25,   # Minimum cover (mm)
            }
        
        else:
            raise ValueError(f"Design code {self.design_code} not supported")
    
    def design_beam_flexure(self, element: Element, material: Material, section: Section,
                           moment_u: float, shear_u: float, axial_u: float = 0.0) -> Dict:
        """Design beam for flexure"""
        
        # Get section dimensions from stored dimensions
        dims = section.dimensions
        b = dims.get("width", 300)  # mm
        h = dims.get("height", 450)  # mm
        d = h - 50  # Effective depth (assuming 50mm cover + reinforcement)
        
        # Material properties
        fck = material.compressive_strength  # N/mm²
        fy = material.yield_strength or 415  # N/mm² (default Fe415)
        
        # Design constants
        gamma_c = self.design_constants["gamma_c"]
        gamma_s = self.design_constants["gamma_s"]
        alpha = self.design_constants["alpha"]
        k_max = self.design_constants["k_max"]
        
        # Design stresses
        if self.design_code == "IS456":
            fcd = 0.67 * fck / gamma_c  # Design compressive strength
            fyd = fy / gamma_s          # Design yield strength
        elif self.design_code == "ACI318":
            fcd = 0.85 * fck * gamma_c  # Design compressive strength
            fyd = fy * gamma_s          # Design yield strength
        else:  # EC2
            fcd = alpha * fck / gamma_c
            fyd = fy / gamma_s
        
        # Calculate required reinforcement
        moment_u_abs = abs(moment_u) * 1e6  # Convert to N-mm
        
        # Limiting moment of resistance
        k_lim = k_max
        mu_lim = 0.36 * fcd * b * d * d * k_lim * (1 - 0.42 * k_lim)
        
        # Check if compression steel is required
        if moment_u_abs > mu_lim:
            # Compression steel required
            mu1 = mu_lim
            mu2 = moment_u_abs - mu_lim
            
            # Tension steel for mu_lim
            ast1 = (0.36 * fcd * b * d * k_lim) / fyd
            
            # Additional tension steel for mu2
            d_prime = 50  # Cover + bar dia + stirrup dia
            ast2 = mu2 / (fyd * (d - d_prime))
            
            # Compression steel
            asc = ast2
            
            # Total tension steel
            ast_total = ast1 + ast2
            
            design_type = "doubly_reinforced"
        
        else:
            # Singly reinforced section
            # Calculate k using quadratic formula
            # mu = 0.36 * fcd * b * d² * k * (1 - 0.42 * k)
            # Rearranging: 0.1512 * fcd * b * d² * k² - 0.36 * fcd * b * d² * k + moment_u = 0
            
            a_coeff = 0.1512 * fcd * b * d * d
            b_coeff = -0.36 * fcd * b * d * d
            c_coeff = moment_u_abs
            
            discriminant = b_coeff * b_coeff - 4 * a_coeff * c_coeff
            
            if discriminant < 0:
                k = 0  # No solution
                ast_total = moment_u_abs / (fyd * 0.9 * d)  # Approximate
            else:
                k = (-b_coeff - math.sqrt(discriminant)) / (2 * a_coeff)
                ast_total = (0.36 * fcd * b * d * k) / fyd
            
            asc = 0
            design_type = "singly_reinforced"
        
        # Calculate reinforcement ratio
        rho = ast_total / (b * d) * 100  # Percentage
        
        # Minimum reinforcement check
        if self.design_code == "IS456":
            ast_min = max(0.85 * b * d / fy, 0.002 * b * h)
        elif self.design_code == "ACI318":
            ast_min = max(1.4 * b * d / fy, 0.0018 * b * h)
        else:  # EC2
            ast_min = max(0.26 * (fck/fy)**0.5 * b * d, 0.0013 * b * d)
        
        ast_provided = max(ast_total, ast_min)
        
        # Design check
        utilization_ratio = moment_u_abs / mu_lim if design_type == "singly_reinforced" else moment_u_abs / (mu_lim + moment_u_abs - mu_lim)
        design_passed = utilization_ratio <= 1.0 and rho <= 4.0  # 4% max reinforcement
        
        return {
            "design_type": design_type,
            "ast_required": ast_total,
            "ast_provided": ast_provided,
            "asc_required": asc,
            "reinforcement_ratio": rho,
            "utilization_ratio": utilization_ratio,
            "design_passed": design_passed,
            "moment_capacity": mu_lim,
            "design_details": {
                "b": b,
                "h": h,
                "d": d,
                "fck": fck,
                "fy": fy,
                "fcd": fcd,
                "fyd": fyd
            }
        }
    
    def design_beam_shear(self, element: Element, material: Material, section: Section,
                         shear_u: float, ast_provided: float) -> Dict:
        """Design beam for shear"""
        
        dims = section.dimensions
        b = dims.get("width", 300)  # mm
        h = dims.get("height", 450)  # mm
        d = h - 50  # Effective depth
        
        # Material properties
        fck = material.compressive_strength
        fy_stirrup = 415  # Fe415 for stirrups
        
        # Design constants
        gamma_c = self.design_constants["gamma_c"]
        tau_c_max = self.design_constants["tau_c_max"]
        
        # Shear stress
        shear_u_abs = abs(shear_u) * 1000  # Convert to N
        tau_v = shear_u_abs / (b * d)  # N/mm²
        
        # Concrete shear strength
        rho = ast_provided / (b * d)  # Reinforcement ratio
        
        if self.design_code == "IS456":
            # IS 456 Table 19
            if fck == 15:
                tau_c_table = [0.28, 0.35, 0.42, 0.49, 0.56]
            elif fck == 20:
                tau_c_table = [0.30, 0.38, 0.45, 0.53, 0.60]
            elif fck == 25:
                tau_c_table = [0.32, 0.40, 0.48, 0.56, 0.64]
            else:
                tau_c_table = [0.36, 0.45, 0.54, 0.63, 0.72]  # For fck >= 30
            
            # Interpolate based on reinforcement ratio
            rho_percent = rho * 100
            if rho_percent <= 0.25:
                tau_c = tau_c_table[0]
            elif rho_percent <= 0.5:
                tau_c = tau_c_table[1]
            elif rho_percent <= 0.75:
                tau_c = tau_c_table[2]
            elif rho_percent <= 1.0:
                tau_c = tau_c_table[3]
            else:
                tau_c = tau_c_table[4]
            
            # Enhancement factor for member thickness
            if h < 300:
                k_factor = 1.0
            else:
                k_factor = min(1.3, (300/h)**0.25)
            
            tau_c *= k_factor
        
        elif self.design_code == "ACI318":
            tau_c = 0.17 * math.sqrt(fck)  # √f'c in MPa
        
        else:  # EC2
            tau_c = 0.18 * (1 + math.sqrt(200/d)) * (100 * rho * fck)**(1/3) / gamma_c
        
        # Check if shear reinforcement is required
        if tau_v <= tau_c:
            # No shear reinforcement required
            stirrup_spacing = "Not required"
            stirrup_diameter = "Not required"
            shear_reinforcement_ratio = 0
            design_passed = True
        
        else:
            # Shear reinforcement required
            tau_v_excess = tau_v - tau_c
            
            # Calculate stirrup requirements
            # Asv/sv = (tau_v_excess * b) / (0.87 * fy_stirrup)
            asv_sv_required = (tau_v_excess * b) / (0.87 * fy_stirrup)
            
            # Assume 8mm 2-legged stirrups
            stirrup_diameter = 8
            asv = 2 * math.pi * (stirrup_diameter/2)**2  # Area of 2-legged stirrup
            
            # Calculate spacing
            sv_required = asv / asv_sv_required
            
            # Maximum spacing limits
            if self.design_code == "IS456":
                sv_max = min(0.75 * d, 300)  # mm
            elif self.design_code == "ACI318":
                sv_max = min(d/2, 600)  # mm
            else:  # EC2
                sv_max = min(0.75 * d, 400)  # mm
            
            stirrup_spacing = min(sv_required, sv_max)
            shear_reinforcement_ratio = asv / (b * stirrup_spacing)
            
            # Check maximum shear strength
            tau_v_max = tau_c_max if self.design_code == "IS456" else 0.66 * math.sqrt(fck)
            design_passed = tau_v <= tau_v_max
        
        return {
            "tau_v": tau_v,
            "tau_c": tau_c,
            "stirrup_diameter": stirrup_diameter,
            "stirrup_spacing": stirrup_spacing,
            "shear_reinforcement_ratio": shear_reinforcement_ratio,
            "design_passed": design_passed,
            "utilization_ratio": tau_v / tau_c_max if isinstance(tau_c_max, (int, float)) else tau_v / (0.66 * math.sqrt(fck))
        }
    
    def design_column(self, element: Element, material: Material, section: Section,
                     axial_u: float, moment_u_x: float, moment_u_y: float) -> Dict:
        """Design column for axial load and biaxial bending"""
        
        dims = section.dimensions
        b = dims.get("width", 300)   # mm
        h = dims.get("height", 300)  # mm
        
        # Calculate effective length
        length = self._calculate_element_length(element)
        lex = ley = length * 1000  # Convert to mm, assume braced in both directions
        
        # Slenderness ratios
        slenderness_x = lex / h
        slenderness_y = ley / b
        
        # Check if short or slender column
        if self.design_code == "IS456":
            slenderness_limit = 12
        else:
            slenderness_limit = 22
        
        is_short_column = max(slenderness_x, slenderness_y) <= slenderness_limit
        
        # Material properties
        fck = material.compressive_strength
        fy = material.yield_strength or 415
        
        # Design for axial load and moment
        axial_u_abs = abs(axial_u) * 1000  # Convert to N
        moment_u_x_abs = abs(moment_u_x) * 1e6  # Convert to N-mm
        moment_u_y_abs = abs(moment_u_y) * 1e6  # Convert to N-mm
        
        # Calculate required reinforcement
        if is_short_column:
            # Short column design
            if moment_u_x_abs == 0 and moment_u_y_abs == 0:
                # Pure compression
                fcd = 0.67 * fck / self.design_constants["gamma_c"]
                fyd = fy / self.design_constants["gamma_s"]
                
                # Approximate formula for tied columns
                ast_required = (axial_u_abs - 0.4 * fcd * (b * h - ast_required)) / (fyd - 0.67 * fcd)
                # Iterative solution needed, simplified here
                ast_required = max(0.008 * b * h, axial_u_abs * 0.01 / fyd)  # Simplified
            
            else:
                # Column with moments - interaction diagram approach
                # Simplified approach using equivalent uniaxial moment
                moment_equiv = math.sqrt(moment_u_x_abs**2 + moment_u_y_abs**2)
                
                # Approximate reinforcement
                ast_required = max(
                    0.008 * b * h,  # Minimum 0.8%
                    (axial_u_abs * 0.01 + moment_equiv * 0.001) / fy  # Approximate
                )
        
        else:
            # Slender column - add moment magnification
            magnification_factor = 1 + 0.01 * max(slenderness_x, slenderness_y)
            moment_u_x_magnified = moment_u_x_abs * magnification_factor
            moment_u_y_magnified = moment_u_y_abs * magnification_factor
            
            moment_equiv = math.sqrt(moment_u_x_magnified**2 + moment_u_y_magnified**2)
            ast_required = max(
                0.008 * b * h,
                (axial_u_abs * 0.01 + moment_equiv * 0.001) / fy
            )
        
        # Maximum reinforcement limit
        ast_max = 0.04 * b * h  # 4% maximum
        ast_provided = min(ast_required, ast_max)
        
        # Calculate reinforcement ratio
        rho = ast_provided / (b * h) * 100
        
        # Design capacity check (simplified)
        design_capacity = 0.4 * 0.67 * fck * (b * h - ast_provided) + 0.67 * fy * ast_provided
        utilization_ratio = axial_u_abs / design_capacity
        design_passed = utilization_ratio <= 1.0 and 0.8 <= rho <= 4.0
        
        return {
            "ast_required": ast_required,
            "ast_provided": ast_provided,
            "reinforcement_ratio": rho,
            "slenderness_x": slenderness_x,
            "slenderness_y": slenderness_y,
            "is_short_column": is_short_column,
            "utilization_ratio": utilization_ratio,
            "design_passed": design_passed,
            "design_capacity": design_capacity,
            "column_type": "short" if is_short_column else "slender"
        }
    
    def _calculate_element_length(self, element: Element) -> float:
        """Calculate element length from start and end nodes"""
        # This would need to access node coordinates
        # Simplified for now
        return 3.0  # Assume 3m length
    
    def generate_design_summary(self, design_results: List[Dict]) -> Dict:
        """Generate design summary report"""
        
        total_elements = len(design_results)
        passed_elements = sum(1 for result in design_results if result.get("design_passed", False))
        
        max_utilization = max(result.get("utilization_ratio", 0) for result in design_results)
        avg_utilization = sum(result.get("utilization_ratio", 0) for result in design_results) / total_elements
        
        return {
            "total_elements_designed": total_elements,
            "elements_passed": passed_elements,
            "elements_failed": total_elements - passed_elements,
            "pass_percentage": (passed_elements / total_elements) * 100,
            "max_utilization_ratio": max_utilization,
            "average_utilization_ratio": avg_utilization,
            "design_code": self.design_code,
            "critical_elements": [
                result for result in design_results 
                if result.get("utilization_ratio", 0) > 0.9
            ]
        }
