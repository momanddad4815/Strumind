import math
from typing import Dict, List, Tuple, Optional
import numpy as np
from backend.db.models import Element, Material, Section, DesignResult


class SteelDesigner:
    """Steel Design Engine supporting multiple international codes"""
    
    def __init__(self, design_code: str = "IS800"):
        self.design_code = design_code
        self.design_constants = self._get_design_constants()
    
    def _get_design_constants(self) -> Dict:
        """Get design constants based on code"""
        
        if self.design_code == "IS800":
            return {
                "gamma_m0": 1.10,  # Partial safety factor for material strength
                "gamma_m1": 1.25,  # Partial safety factor for member buckling
                "alpha": 0.2,      # Imperfection factor for buckling curves
                "beta": 1.0,       # Lateral torsional buckling factor
            }
        
        elif self.design_code == "AISC360":
            return {
                "phi_b": 0.90,     # Resistance factor for flexure
                "phi_c": 0.90,     # Resistance factor for compression
                "phi_t": 0.90,     # Resistance factor for tension
                "alpha": 0.34,     # Imperfection factor
                "cb": 1.0,         # Lateral torsional buckling modification factor
            }
        
        elif self.design_code == "EC3":
            return {
                "gamma_m0": 1.00,  # Partial safety factor for cross-section
                "gamma_m1": 1.00,  # Partial safety factor for member buckling
                "alpha": 0.34,     # Imperfection factor for buckling curve 'b'
                "beta": 1.0,       # Equivalent uniform moment factor
            }
        
        else:
            raise ValueError(f"Design code {self.design_code} not supported")
    
    def design_beam_flexure(self, element: Element, material: Material, section: Section,
                           moment_u: float, shear_u: float) -> Dict:
        """Design steel beam for flexure"""
        
        # Section properties
        fy = material.yield_strength  # N/mm²
        fu = material.ultimate_strength  # N/mm²
        E = material.elastic_modulus   # N/mm²
        
        # Section properties (convert from mm⁴ to m⁴ then back to mm⁴)
        Zx = section.section_modulus_y or (section.moment_of_inertia_y / (section.dimensions.get("depth", 200) / 2))
        Zy = section.section_modulus_z or (section.moment_of_inertia_z / (section.dimensions.get("width", 100) / 2))
        
        # Design moment
        moment_u_abs = abs(moment_u) * 1e6  # Convert to N-mm
        
        # Calculate moment capacity
        if self.design_code == "IS800":
            # IS 800 design
            gamma_m0 = self.design_constants["gamma_m0"]
            
            # Check for local buckling
            # Simplified - assume compact section
            beta_b = 1.0  # Bending strength reduction factor
            
            # Design bending strength
            Md = beta_b * Zx * fy / gamma_m0
            
            # Lateral torsional buckling check
            # Simplified - assume adequate lateral support
            fbd = fy  # Allowable bending stress
            
            # Design moment capacity
            moment_capacity = Md
        
        elif self.design_code == "AISC360":
            # AISC 360 design
            phi_b = self.design_constants["phi_b"]
            
            # Nominal flexural strength
            # Assume compact section (Lb <= Lp)
            Mp = Zx * fy  # Plastic moment
            Mn = Mp
            
            # Design moment capacity
            moment_capacity = phi_b * Mn
        
        else:  # EC3
            # Eurocode 3 design
            gamma_m0 = self.design_constants["gamma_m0"]
            
            # Cross-section classification (assume Class 1 - plastic)
            class_section = 1
            
            if class_section <= 2:
                # Plastic or compact section
                Mrd = Zx * fy / gamma_m0
            else:
                # Semi-compact or slender section
                Weff = Zx * 0.9  # Effective section modulus (simplified)
                Mrd = Weff * fy / gamma_m0
            
            moment_capacity = Mrd
        
        # Design check
        utilization_ratio = moment_u_abs / moment_capacity
        design_passed = utilization_ratio <= 1.0
        
        # Deflection check (simplified)
        # L/250 for live load, L/350 for total load
        length = self._calculate_element_length(element) * 1000  # mm
        I = section.moment_of_inertia_y / 1e12 * 1e12  # mm⁴
        
        # Approximate deflection for UDL (5wL⁴/384EI)
        w_equivalent = moment_u_abs / (length**2 / 8)  # Equivalent UDL
        deflection = 5 * w_equivalent * length**4 / (384 * E * I)
        
        deflection_limit = length / 250  # L/250
        deflection_ok = deflection <= deflection_limit
        
        return {
            "moment_capacity": moment_capacity,
            "moment_demand": moment_u_abs,
            "utilization_ratio": utilization_ratio,
            "design_passed": design_passed,
            "deflection": deflection,
            "deflection_limit": deflection_limit,
            "deflection_ok": deflection_ok,
            "section_class": getattr(self, 'class_section', 1),
            "design_details": {
                "fy": fy,
                "fu": fu,
                "Zx": Zx,
                "design_code": self.design_code
            }
        }
    
    def design_beam_shear(self, element: Element, material: Material, section: Section,
                         shear_u: float) -> Dict:
        """Design steel beam for shear"""
        
        # Material properties
        fy = material.yield_strength
        
        # Section properties
        dims = section.dimensions
        h = dims.get("depth", 200)  # mm
        tw = dims.get("web_thickness", 6)  # mm
        
        # Shear area (approximate)
        Av = h * tw  # Web area
        
        # Design shear
        shear_u_abs = abs(shear_u) * 1000  # Convert to N
        
        # Calculate shear capacity
        if self.design_code == "IS800":
            # IS 800 design
            gamma_m0 = self.design_constants["gamma_m0"]
            
            # Design shear strength
            Vd = Av * fy / (math.sqrt(3) * gamma_m0)
        
        elif self.design_code == "AISC360":
            # AISC 360 design
            phi_v = 0.90  # Resistance factor for shear
            
            # Nominal shear strength
            # Check web slenderness
            h_tw = h / tw
            kv = 5.0  # Shear buckling coefficient (simplified)
            
            if h_tw <= 2.24 * math.sqrt(E / fy):
                # Web yielding
                Vn = 0.6 * fy * Av
            else:
                # Web buckling
                Cv = min(1.0, 5.0 / (h_tw / math.sqrt(E / fy))**2)
                Vn = 0.6 * fy * Av * Cv
            
            Vd = phi_v * Vn
        
        else:  # EC3
            # Eurocode 3 design
            gamma_m0 = self.design_constants["gamma_m0"]
            
            # Design shear resistance
            Vrd = Av * (fy / math.sqrt(3)) / gamma_m0
            Vd = Vrd
        
        # Design check
        utilization_ratio = shear_u_abs / Vd
        design_passed = utilization_ratio <= 1.0
        
        return {
            "shear_capacity": Vd,
            "shear_demand": shear_u_abs,
            "utilization_ratio": utilization_ratio,
            "design_passed": design_passed,
            "shear_area": Av,
            "web_slenderness": h / tw,
            "design_details": {
                "fy": fy,
                "h": h,
                "tw": tw,
                "design_code": self.design_code
            }
        }
    
    def design_column(self, element: Element, material: Material, section: Section,
                     axial_u: float, moment_u_x: float, moment_u_y: float) -> Dict:
        """Design steel column for axial load and bending"""
        
        # Material properties
        fy = material.yield_strength
        E = material.elastic_modulus
        
        # Section properties
        A = section.area / 1e6 * 1e6  # mm²
        rx = math.sqrt(section.moment_of_inertia_y / A)  # Radius of gyration
        ry = math.sqrt(section.moment_of_inertia_z / A)
        Zx = section.section_modulus_y
        Zy = section.section_modulus_z
        
        # Element length
        length = self._calculate_element_length(element) * 1000  # mm
        
        # Effective lengths (assume K = 1.0 for both axes)
        Kx = Ky = 1.0
        Lx = Kx * length
        Ly = Ky * length
        
        # Slenderness ratios
        slenderness_x = Lx / rx
        slenderness_y = Ly / ry
        slenderness_max = max(slenderness_x, slenderness_y)
        
        # Design forces
        axial_u_abs = abs(axial_u) * 1000  # Convert to N
        moment_u_x_abs = abs(moment_u_x) * 1e6  # Convert to N-mm
        moment_u_y_abs = abs(moment_u_y) * 1e6  # Convert to N-mm
        
        # Calculate compression capacity
        if self.design_code == "IS800":
            # IS 800 design
            gamma_m0 = self.design_constants["gamma_m0"]
            gamma_m1 = self.design_constants["gamma_m1"]
            
            # Non-dimensional slenderness
            lambda_bar = (slenderness_max / math.pi) * math.sqrt(fy / E)
            
            # Buckling curve selection (assume curve 'b')
            alpha = 0.34
            phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
            chi = min(1.0, 1 / (phi + math.sqrt(phi**2 - lambda_bar**2)))
            
            # Design compressive strength
            Pd = chi * A * fy / gamma_m1
        
        elif self.design_code == "AISC360":
            # AISC 360 design
            phi_c = self.design_constants["phi_c"]
            
            # Elastic buckling stress
            Fe = math.pi**2 * E / slenderness_max**2
            
            # Critical stress
            if slenderness_max <= 4.71 * math.sqrt(E / fy):
                # Inelastic buckling
                Fcr = (0.658**(fy/Fe)) * fy
            else:
                # Elastic buckling
                Fcr = 0.877 * Fe
            
            # Nominal compressive strength
            Pn = Fcr * A
            Pd = phi_c * Pn
        
        else:  # EC3
            # Eurocode 3 design
            gamma_m1 = self.design_constants["gamma_m1"]
            
            # Non-dimensional slenderness
            lambda_bar = (slenderness_max / math.pi) * math.sqrt(fy / E)
            
            # Reduction factor for buckling
            alpha = 0.34  # Buckling curve 'b'
            phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
            chi = min(1.0, 1 / (phi + math.sqrt(phi**2 - lambda_bar**2)))
            
            # Design buckling resistance
            Pd = chi * A * fy / gamma_m1
        
        # Calculate moment capacities (same as beam design)
        if self.design_code == "IS800":
            Mdx = Zx * fy / gamma_m0
            Mdy = Zy * fy / gamma_m0
        elif self.design_code == "AISC360":
            phi_b = 0.90
            Mdx = phi_b * Zx * fy
            Mdy = phi_b * Zy * fy
        else:  # EC3
            gamma_m0 = self.design_constants["gamma_m0"]
            Mdx = Zx * fy / gamma_m0
            Mdy = Zy * fy / gamma_m0
        
        # Interaction check
        axial_ratio = axial_u_abs / Pd
        moment_ratio_x = moment_u_x_abs / Mdx
        moment_ratio_y = moment_u_y_abs / Mdy
        
        # Simplified interaction equation
        if axial_ratio >= 0.2:
            # High axial load
            interaction_ratio = axial_ratio + (8/9) * (moment_ratio_x + moment_ratio_y)
        else:
            # Low axial load
            interaction_ratio = axial_ratio/2 + (moment_ratio_x + moment_ratio_y)
        
        utilization_ratio = interaction_ratio
        design_passed = utilization_ratio <= 1.0
        
        return {
            "compression_capacity": Pd,
            "moment_capacity_x": Mdx,
            "moment_capacity_y": Mdy,
            "axial_demand": axial_u_abs,
            "moment_demand_x": moment_u_x_abs,
            "moment_demand_y": moment_u_y_abs,
            "slenderness_x": slenderness_x,
            "slenderness_y": slenderness_y,
            "slenderness_max": slenderness_max,
            "buckling_factor": chi if self.design_code != "AISC360" else Fcr/fy,
            "axial_ratio": axial_ratio,
            "moment_ratio_x": moment_ratio_x,
            "moment_ratio_y": moment_ratio_y,
            "interaction_ratio": interaction_ratio,
            "utilization_ratio": utilization_ratio,
            "design_passed": design_passed
        }
    
    def design_tension_member(self, element: Element, material: Material, section: Section,
                             tension_u: float) -> Dict:
        """Design steel tension member"""
        
        # Material properties
        fy = material.yield_strength
        fu = material.ultimate_strength
        
        # Section properties
        A = section.area / 1e6 * 1e6  # mm²
        
        # Design tension
        tension_u_abs = abs(tension_u) * 1000  # Convert to N
        
        # Calculate tension capacity
        if self.design_code == "IS800":
            # IS 800 design
            gamma_m0 = self.design_constants["gamma_m0"]
            gamma_m1 = self.design_constants["gamma_m1"]
            
            # Design strength governed by:
            # 1. Yielding of gross section
            Tdg = A * fy / gamma_m0
            
            # 2. Rupture of net section (assume no holes for simplification)
            An = A  # Net area = gross area (no holes)
            Tdn = 0.9 * An * fu / gamma_m1
            
            # Design tension capacity
            Td = min(Tdg, Tdn)
        
        elif self.design_code == "AISC360":
            # AISC 360 design
            phi_t = self.design_constants["phi_t"]
            
            # Nominal tensile strength
            # 1. Yielding in gross section
            Pn1 = fy * A
            
            # 2. Fracture in net section
            An = A  # Assume no holes
            Pn2 = fu * An
            
            Pn = min(Pn1, Pn2)
            Td = phi_t * Pn
        
        else:  # EC3
            # Eurocode 3 design
            gamma_m0 = self.design_constants["gamma_m0"]
            gamma_m2 = 1.25  # For net section
            
            # Design tension resistance
            # 1. Gross section yielding
            Ntrd1 = A * fy / gamma_m0
            
            # 2. Net section fracture
            An = A  # Assume no holes
            Ntrd2 = 0.9 * An * fu / gamma_m2
            
            Td = min(Ntrd1, Ntrd2)
        
        # Design check
        utilization_ratio = tension_u_abs / Td
        design_passed = utilization_ratio <= 1.0
        
        return {
            "tension_capacity": Td,
            "tension_demand": tension_u_abs,
            "utilization_ratio": utilization_ratio,
            "design_passed": design_passed,
            "governing_limit": "yielding" if Td == A * fy / self.design_constants.get("gamma_m0", 1.1) else "fracture",
            "design_details": {
                "fy": fy,
                "fu": fu,
                "A": A,
                "design_code": self.design_code
            }
        }
    
    def _calculate_element_length(self, element: Element) -> float:
        """Calculate element length from start and end nodes"""
        # Simplified for now
        return 3.0  # Assume 3m length
    
    def check_deflection(self, element: Element, section: Section, loads: List[Dict]) -> Dict:
        """Check deflection limits for steel members"""
        
        E = 200000  # N/mm² for steel
        I = section.moment_of_inertia_y / 1e12 * 1e12  # mm⁴
        length = self._calculate_element_length(element) * 1000  # mm
        
        # Calculate deflection for different load types
        max_deflection = 0
        
        for load in loads:
            if load["type"] == "udl":
                # Uniform distributed load: 5wL⁴/384EI
                w = load["magnitude"]  # N/mm
                deflection = 5 * w * length**4 / (384 * E * I)
            elif load["type"] == "point":
                # Point load at center: PL³/48EI
                P = load["magnitude"]  # N
                deflection = P * length**3 / (48 * E * I)
            else:
                deflection = 0
            
            max_deflection = max(max_deflection, deflection)
        
        # Deflection limits
        deflection_limit_live = length / 250  # L/250 for live load
        deflection_limit_total = length / 350  # L/350 for total load
        
        return {
            "max_deflection": max_deflection,
            "deflection_limit_live": deflection_limit_live,
            "deflection_limit_total": deflection_limit_total,
            "deflection_ok": max_deflection <= deflection_limit_total,
            "deflection_ratio": max_deflection / deflection_limit_total
        }
    
    def generate_design_summary(self, design_results: List[Dict]) -> Dict:
        """Generate design summary report"""
        
        total_elements = len(design_results)
        passed_elements = sum(1 for result in design_results if result.get("design_passed", False))
        
        max_utilization = max(result.get("utilization_ratio", 0) for result in design_results)
        avg_utilization = sum(result.get("utilization_ratio", 0) for result in design_results) / total_elements
        
        # Categorize elements by utilization
        over_utilized = [r for r in design_results if r.get("utilization_ratio", 0) > 1.0]
        highly_utilized = [r for r in design_results if 0.9 <= r.get("utilization_ratio", 0) <= 1.0]
        under_utilized = [r for r in design_results if r.get("utilization_ratio", 0) < 0.5]
        
        return {
            "total_elements_designed": total_elements,
            "elements_passed": passed_elements,
            "elements_failed": total_elements - passed_elements,
            "pass_percentage": (passed_elements / total_elements) * 100,
            "max_utilization_ratio": max_utilization,
            "average_utilization_ratio": avg_utilization,
            "design_code": self.design_code,
            "over_utilized_count": len(over_utilized),
            "highly_utilized_count": len(highly_utilized),
            "under_utilized_count": len(under_utilized),
            "critical_elements": over_utilized + highly_utilized
        }
