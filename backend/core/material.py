from typing import List, Optional, Dict, Any
from backend.db.models import Material, MaterialType
from sqlalchemy.orm import Session


class MaterialLibrary:
    """Predefined material properties based on international standards"""
    
    @staticmethod
    def get_concrete_materials():
        return {
            # IS 456 (Indian Standard)
            "M15": {"fck": 15, "elastic_modulus": 22360, "density": 25, "design_code": "IS456"},
            "M20": {"fck": 20, "elastic_modulus": 27386, "density": 25, "design_code": "IS456"},
            "M25": {"fck": 25, "elastic_modulus": 31623, "density": 25, "design_code": "IS456"},
            "M30": {"fck": 30, "elastic_modulus": 35355, "density": 25, "design_code": "IS456"},
            "M35": {"fck": 35, "elastic_modulus": 38730, "density": 25, "design_code": "IS456"},
            "M40": {"fck": 40, "elastic_modulus": 41833, "density": 25, "design_code": "IS456"},
            "M45": {"fck": 45, "elastic_modulus": 44721, "density": 25, "design_code": "IS456"},
            "M50": {"fck": 50, "elastic_modulus": 47434, "density": 25, "design_code": "IS456"},
            
            # ACI 318 (American Concrete Institute)
            "3000psi": {"fck": 20.7, "elastic_modulus": 24855, "density": 23.56, "design_code": "ACI318"},
            "4000psi": {"fck": 27.6, "elastic_modulus": 28728, "density": 23.56, "design_code": "ACI318"},
            "5000psi": {"fck": 34.5, "elastic_modulus": 32139, "density": 23.56, "design_code": "ACI318"},
            "6000psi": {"fck": 41.4, "elastic_modulus": 35217, "density": 23.56, "design_code": "ACI318"},
            
            # Eurocode 2
            "C20/25": {"fck": 20, "elastic_modulus": 30000, "density": 25, "design_code": "EC2"},
            "C25/30": {"fck": 25, "elastic_modulus": 31000, "density": 25, "design_code": "EC2"},
            "C30/37": {"fck": 30, "elastic_modulus": 33000, "density": 25, "design_code": "EC2"},
            "C35/45": {"fck": 35, "elastic_modulus": 34000, "density": 25, "design_code": "EC2"},
            "C40/50": {"fck": 40, "elastic_modulus": 35000, "density": 25, "design_code": "EC2"},
        }
    
    @staticmethod
    def get_steel_materials():
        return {
            # IS 800 (Indian Standard)
            "Fe250": {"fy": 250, "fu": 410, "elastic_modulus": 200000, "density": 78.5, "design_code": "IS800"},
            "Fe415": {"fy": 415, "fu": 485, "elastic_modulus": 200000, "density": 78.5, "design_code": "IS800"},
            "Fe500": {"fy": 500, "fu": 545, "elastic_modulus": 200000, "density": 78.5, "design_code": "IS800"},
            "Fe550": {"fy": 550, "fu": 585, "elastic_modulus": 200000, "density": 78.5, "design_code": "IS800"},
            
            # AISC 360 (American Institute of Steel Construction)
            "A36": {"fy": 248, "fu": 400, "elastic_modulus": 200000, "density": 78.5, "design_code": "AISC360"},
            "A572_Gr50": {"fy": 345, "fu": 450, "elastic_modulus": 200000, "density": 78.5, "design_code": "AISC360"},
            "A992": {"fy": 345, "fu": 450, "elastic_modulus": 200000, "density": 78.5, "design_code": "AISC360"},
            
            # Eurocode 3
            "S235": {"fy": 235, "fu": 360, "elastic_modulus": 210000, "density": 78.5, "design_code": "EC3"},
            "S275": {"fy": 275, "fu": 430, "elastic_modulus": 210000, "density": 78.5, "design_code": "EC3"},
            "S355": {"fy": 355, "fu": 510, "elastic_modulus": 210000, "density": 78.5, "design_code": "EC3"},
            "S450": {"fy": 440, "fu": 550, "elastic_modulus": 210000, "density": 78.5, "design_code": "EC3"},
        }
    
    @staticmethod
    def get_timber_materials():
        return {
            # Typical softwood properties
            "Southern_Pine": {"fc": 35, "ft": 20, "elastic_modulus": 12000, "density": 6, "design_code": "NDS"},
            "Douglas_Fir": {"fc": 40, "ft": 24, "elastic_modulus": 13000, "density": 6.5, "design_code": "NDS"},
            "Hem_Fir": {"fc": 32, "ft": 18, "elastic_modulus": 11000, "density": 5.5, "design_code": "NDS"},
            
            # Engineered lumber
            "LVL": {"fc": 50, "ft": 35, "elastic_modulus": 14000, "density": 6.5, "design_code": "NDS"},
            "PSL": {"fc": 45, "ft": 30, "elastic_modulus": 13500, "density": 6.2, "design_code": "NDS"},
            "LSL": {"fc": 40, "ft": 25, "elastic_modulus": 12500, "density": 6.0, "design_code": "NDS"},
        }


class MaterialManager:
    def __init__(self, db_session: Session, model_id: int):
        self.db = db_session
        self.model_id = model_id
        self._materials_cache = {}
        self._load_materials()
    
    def _load_materials(self):
        materials = self.db.query(Material).filter(Material.model_id == self.model_id).all()
        for material in materials:
            self._materials_cache[material.id] = material
    
    def create_material(self, name: str, material_type: MaterialType,
                       elastic_modulus: float, poisson_ratio: float, density: float,
                       yield_strength: float = None, ultimate_strength: float = None,
                       compressive_strength: float = None, design_code: str = None,
                       grade: str = None, thermal_expansion: float = None) -> Material:
        
        material = Material(
            model_id=self.model_id,
            name=name,
            material_type=material_type,
            elastic_modulus=elastic_modulus,
            poisson_ratio=poisson_ratio,
            density=density,
            yield_strength=yield_strength,
            ultimate_strength=ultimate_strength,
            compressive_strength=compressive_strength,
            design_code=design_code,
            grade=grade,
            thermal_expansion=thermal_expansion
        )
        
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)
        
        self._materials_cache[material.id] = material
        return material
    
    def create_from_library(self, name: str, material_type: MaterialType, grade: str) -> Material:
        """Create material from predefined library"""
        
        if material_type == MaterialType.CONCRETE:
            library = MaterialLibrary.get_concrete_materials()
        elif material_type == MaterialType.STEEL:
            library = MaterialLibrary.get_steel_materials()
        elif material_type == MaterialType.TIMBER:
            library = MaterialLibrary.get_timber_materials()
        else:
            raise ValueError(f"Material type {material_type} not supported in library")
        
        if grade not in library:
            raise ValueError(f"Grade {grade} not found in {material_type} library")
        
        props = library[grade]
        
        # Map library properties to material properties
        if material_type == MaterialType.CONCRETE:
            return self.create_material(
                name=name,
                material_type=material_type,
                elastic_modulus=props["elastic_modulus"] * 1000,  # Convert to kN/m²
                poisson_ratio=0.2,  # Typical for concrete
                density=props["density"],
                compressive_strength=props["fck"],
                design_code=props["design_code"],
                grade=grade,
                thermal_expansion=1e-5  # Typical for concrete
            )
        
        elif material_type == MaterialType.STEEL:
            return self.create_material(
                name=name,
                material_type=material_type,
                elastic_modulus=props["elastic_modulus"] * 1000,  # Convert to kN/m²
                poisson_ratio=0.3,  # Typical for steel
                density=props["density"],
                yield_strength=props["fy"],
                ultimate_strength=props["fu"],
                design_code=props["design_code"],
                grade=grade,
                thermal_expansion=1.2e-5  # Typical for steel
            )
        
        elif material_type == MaterialType.TIMBER:
            return self.create_material(
                name=name,
                material_type=material_type,
                elastic_modulus=props["elastic_modulus"] * 1000,  # Convert to kN/m²
                poisson_ratio=0.4,  # Typical for timber
                density=props["density"],
                compressive_strength=props["fc"],
                ultimate_strength=props["ft"],
                design_code=props["design_code"],
                grade=grade,
                thermal_expansion=5e-6  # Typical for timber
            )
    
    def get_material(self, material_id: int) -> Optional[Material]:
        return self._materials_cache.get(material_id)
    
    def get_material_by_name(self, name: str) -> Optional[Material]:
        for material in self._materials_cache.values():
            if material.name == name:
                return material
        return None
    
    def get_all_materials(self) -> List[Material]:
        return list(self._materials_cache.values())
    
    def get_materials_by_type(self, material_type: MaterialType) -> List[Material]:
        return [mat for mat in self._materials_cache.values() if mat.material_type == material_type]
    
    def update_material_properties(self, material_id: int, properties: Dict[str, Any]) -> bool:
        material = self.get_material(material_id)
        if not material:
            return False
        
        for prop, value in properties.items():
            if hasattr(material, prop):
                setattr(material, prop, value)
        
        self.db.commit()
        return True
    
    def delete_material(self, material_id: int) -> bool:
        material = self.get_material(material_id)
        if not material:
            return False
        
        # Check if material is used by elements
        from backend.db.models import Element
        elements_count = self.db.query(Element).filter(Element.material_id == material_id).count()
        
        if elements_count > 0:
            raise ValueError(f"Cannot delete material {material_id}: it is used by {elements_count} elements")
        
        self.db.delete(material)
        self.db.commit()
        
        if material_id in self._materials_cache:
            del self._materials_cache[material_id]
        
        return True
    
    def get_available_grades(self, material_type: MaterialType) -> List[str]:
        """Get available grades from material library"""
        if material_type == MaterialType.CONCRETE:
            return list(MaterialLibrary.get_concrete_materials().keys())
        elif material_type == MaterialType.STEEL:
            return list(MaterialLibrary.get_steel_materials().keys())
        elif material_type == MaterialType.TIMBER:
            return list(MaterialLibrary.get_timber_materials().keys())
        else:
            return []
    
    def get_material_properties(self, material_id: int) -> Optional[Dict[str, Any]]:
        """Get all material properties as dictionary"""
        material = self.get_material(material_id)
        if not material:
            return None
        
        return {
            "id": material.id,
            "name": material.name,
            "material_type": material.material_type,
            "elastic_modulus": material.elastic_modulus,
            "poisson_ratio": material.poisson_ratio,
            "density": material.density,
            "yield_strength": material.yield_strength,
            "ultimate_strength": material.ultimate_strength,
            "compressive_strength": material.compressive_strength,
            "design_code": material.design_code,
            "grade": material.grade,
            "thermal_expansion": material.thermal_expansion
        }
