from typing import List, Optional, Dict, Any
import math
from db.models import Section, SectionType
from sqlalchemy.orm import Session


class SectionLibrary:
    """Predefined section properties based on international standards"""
    
    @staticmethod
    def get_steel_i_sections():
        """Standard I-sections (metric and imperial)"""
        return {
            # Indian Standard I-sections (ISMB)
            "ISMB100": {"depth": 100, "width": 75, "web_thickness": 4.0, "flange_thickness": 7.2},
            "ISMB125": {"depth": 125, "width": 75, "web_thickness": 4.4, "flange_thickness": 8.1},
            "ISMB150": {"depth": 150, "width": 80, "web_thickness": 4.8, "flange_thickness": 9.0},
            "ISMB175": {"depth": 175, "width": 90, "web_thickness": 5.2, "flange_thickness": 9.9},
            "ISMB200": {"depth": 200, "width": 100, "web_thickness": 5.7, "flange_thickness": 10.8},
            "ISMB250": {"depth": 250, "width": 125, "web_thickness": 6.5, "flange_thickness": 12.5},
            "ISMB300": {"depth": 300, "width": 140, "web_thickness": 7.1, "flange_thickness": 13.1},
            "ISMB350": {"depth": 350, "width": 140, "web_thickness": 8.1, "flange_thickness": 14.2},
            "ISMB400": {"depth": 400, "width": 140, "web_thickness": 8.9, "flange_thickness": 16.0},
            "ISMB450": {"depth": 450, "width": 150, "web_thickness": 9.4, "flange_thickness": 17.4},
            "ISMB500": {"depth": 500, "width": 180, "web_thickness": 10.2, "flange_thickness": 17.2},
            "ISMB600": {"depth": 600, "width": 210, "web_thickness": 12.0, "flange_thickness": 20.8},
            
            # American Standard W-sections
            "W8X18": {"depth": 203, "width": 133, "web_thickness": 5.8, "flange_thickness": 8.9},
            "W10X22": {"depth": 254, "width": 146, "web_thickness": 5.8, "flange_thickness": 9.9},
            "W12X26": {"depth": 311, "width": 165, "web_thickness": 6.2, "flange_thickness": 9.9},
            "W14X30": {"depth": 355, "width": 171, "web_thickness": 6.6, "flange_thickness": 10.9},
            "W16X36": {"depth": 403, "width": 178, "web_thickness": 7.6, "flange_thickness": 12.2},
            "W18X40": {"depth": 457, "width": 152, "web_thickness": 8.1, "flange_thickness": 12.7},
            "W21X44": {"depth": 533, "width": 165, "web_thickness": 8.9, "flange_thickness": 11.4},
            "W24X55": {"depth": 610, "width": 178, "web_thickness": 10.7, "flange_thickness": 14.0},
            
            # European I-sections (IPE)
            "IPE100": {"depth": 100, "width": 55, "web_thickness": 4.1, "flange_thickness": 5.7},
            "IPE120": {"depth": 120, "width": 64, "web_thickness": 4.4, "flange_thickness": 6.3},
            "IPE140": {"depth": 140, "width": 73, "web_thickness": 4.7, "flange_thickness": 6.9},
            "IPE160": {"depth": 160, "width": 82, "web_thickness": 5.0, "flange_thickness": 7.4},
            "IPE180": {"depth": 180, "width": 91, "web_thickness": 5.3, "flange_thickness": 8.0},
            "IPE200": {"depth": 200, "width": 100, "web_thickness": 5.6, "flange_thickness": 8.5},
            "IPE220": {"depth": 220, "width": 110, "web_thickness": 5.9, "flange_thickness": 9.2},
            "IPE240": {"depth": 240, "width": 120, "web_thickness": 6.2, "flange_thickness": 9.8},
            "IPE270": {"depth": 270, "width": 135, "web_thickness": 6.6, "flange_thickness": 10.2},
            "IPE300": {"depth": 300, "width": 150, "web_thickness": 7.1, "flange_thickness": 10.7},
            "IPE330": {"depth": 330, "width": 160, "web_thickness": 7.5, "flange_thickness": 11.5},
            "IPE360": {"depth": 360, "width": 170, "web_thickness": 8.0, "flange_thickness": 12.7},
            "IPE400": {"depth": 400, "width": 180, "web_thickness": 8.6, "flange_thickness": 13.5},
            "IPE450": {"depth": 450, "width": 190, "web_thickness": 9.4, "flange_thickness": 14.6},
            "IPE500": {"depth": 500, "width": 200, "web_thickness": 10.2, "flange_thickness": 16.0},
            "IPE550": {"depth": 550, "width": 210, "web_thickness": 11.1, "flange_thickness": 17.2},
            "IPE600": {"depth": 600, "width": 220, "web_thickness": 12.0, "flange_thickness": 19.0},
        }
    
    @staticmethod
    def get_steel_channels():
        """Standard channel sections"""
        return {
            # Indian Standard Channels (ISMC)
            "ISMC75": {"depth": 75, "width": 40, "web_thickness": 4.8, "flange_thickness": 7.5},
            "ISMC100": {"depth": 100, "width": 50, "web_thickness": 5.1, "flange_thickness": 7.5},
            "ISMC125": {"depth": 125, "width": 65, "web_thickness": 5.3, "flange_thickness": 8.1},
            "ISMC150": {"depth": 150, "width": 75, "web_thickness": 5.7, "flange_thickness": 9.0},
            "ISMC175": {"depth": 175, "width": 75, "web_thickness": 6.1, "flange_thickness": 9.8},
            "ISMC200": {"depth": 200, "width": 75, "web_thickness": 6.5, "flange_thickness": 10.5},
            "ISMC250": {"depth": 250, "width": 80, "web_thickness": 7.1, "flange_thickness": 12.5},
            "ISMC300": {"depth": 300, "width": 90, "web_thickness": 7.6, "flange_thickness": 13.6},
            "ISMC350": {"depth": 350, "width": 100, "web_thickness": 8.1, "flange_thickness": 15.3},
            "ISMC400": {"depth": 400, "width": 100, "web_thickness": 8.6, "flange_thickness": 16.5},
            
            # American Standard C-sections
            "C3X4.1": {"depth": 76, "width": 41, "web_thickness": 4.3, "flange_thickness": 6.4},
            "C4X5.4": {"depth": 102, "width": 48, "web_thickness": 4.6, "flange_thickness": 6.6},
            "C5X6.7": {"depth": 127, "width": 51, "web_thickness": 4.8, "flange_thickness": 6.9},
            "C6X8.2": {"depth": 152, "width": 54, "web_thickness": 5.1, "flange_thickness": 7.4},
            "C8X11.5": {"depth": 203, "width": 58, "web_thickness": 5.6, "flange_thickness": 8.9},
            "C10X15.3": {"depth": 254, "width": 67, "web_thickness": 5.8, "flange_thickness": 9.9},
            "C12X20.7": {"depth": 305, "width": 76, "web_thickness": 6.4, "flange_thickness": 10.9},
            "C15X33.9": {"depth": 381, "width": 86, "web_thickness": 9.4, "flange_thickness": 13.0},
        }
    
    @staticmethod
    def get_steel_tubes():
        """Standard tubular sections"""
        return {
            # Circular hollow sections
            "CHS48.3x3.2": {"diameter": 48.3, "thickness": 3.2},
            "CHS60.3x3.6": {"diameter": 60.3, "thickness": 3.6},
            "CHS73.0x3.6": {"diameter": 73.0, "thickness": 3.6},
            "CHS88.9x4.0": {"diameter": 88.9, "thickness": 4.0},
            "CHS101.6x4.0": {"diameter": 101.6, "thickness": 4.0},
            "CHS114.3x4.5": {"diameter": 114.3, "thickness": 4.5},
            "CHS139.7x5.0": {"diameter": 139.7, "thickness": 5.0},
            "CHS168.3x5.6": {"diameter": 168.3, "thickness": 5.6},
            "CHS193.7x6.3": {"diameter": 193.7, "thickness": 6.3},
            "CHS219.1x6.3": {"diameter": 219.1, "thickness": 6.3},
            "CHS244.5x8.0": {"diameter": 244.5, "thickness": 8.0},
            "CHS273.0x8.0": {"diameter": 273.0, "thickness": 8.0},
            "CHS323.9x9.5": {"diameter": 323.9, "thickness": 9.5},
            
            # Rectangular hollow sections
            "RHS50x25x2.5": {"height": 50, "width": 25, "thickness": 2.5},
            "RHS65x35x2.5": {"height": 65, "width": 35, "thickness": 2.5},
            "RHS75x50x3.0": {"height": 75, "width": 50, "thickness": 3.0},
            "RHS100x50x3.0": {"height": 100, "width": 50, "thickness": 3.0},
            "RHS100x75x4.0": {"height": 100, "width": 75, "thickness": 4.0},
            "RHS125x75x4.0": {"height": 125, "width": 75, "thickness": 4.0},
            "RHS150x100x5.0": {"height": 150, "width": 100, "thickness": 5.0},
            "RHS200x100x5.0": {"height": 200, "width": 100, "thickness": 5.0},
            "RHS250x150x6.0": {"height": 250, "width": 150, "thickness": 6.0},
            "RHS300x200x8.0": {"height": 300, "width": 200, "thickness": 8.0},
            
            # Square hollow sections
            "SHS25x25x2.0": {"height": 25, "width": 25, "thickness": 2.0},
            "SHS40x40x2.5": {"height": 40, "width": 40, "thickness": 2.5},
            "SHS50x50x3.0": {"height": 50, "width": 50, "thickness": 3.0},
            "SHS65x65x3.0": {"height": 65, "width": 65, "thickness": 3.0},
            "SHS75x75x4.0": {"height": 75, "width": 75, "thickness": 4.0},
            "SHS100x100x4.0": {"height": 100, "width": 100, "thickness": 4.0},
            "SHS125x125x5.0": {"height": 125, "width": 125, "thickness": 5.0},
            "SHS150x150x6.0": {"height": 150, "width": 150, "thickness": 6.0},
            "SHS200x200x8.0": {"height": 200, "width": 200, "thickness": 8.0},
            "SHS250x250x10.0": {"height": 250, "width": 250, "thickness": 10.0},
        }


class SectionCalculator:
    """Calculate section properties"""
    
    @staticmethod
    def calculate_i_section_properties(depth: float, width: float, 
                                     web_thickness: float, flange_thickness: float) -> Dict[str, float]:
        """Calculate properties of I-section"""
        # Area
        area = 2 * width * flange_thickness + (depth - 2 * flange_thickness) * web_thickness
        
        # Moment of inertia about y-axis (strong axis)
        iy = (width * depth**3 - (width - web_thickness) * (depth - 2 * flange_thickness)**3) / 12
        
        # Moment of inertia about z-axis (weak axis)
        iz = (2 * flange_thickness * width**3 + (depth - 2 * flange_thickness) * web_thickness**3) / 12
        
        # Section modulus
        zy = 2 * iy / depth
        zz = 2 * iz / width
        
        # Torsional constant (approximate)
        j = (2 * width * flange_thickness**3 + (depth - 2 * flange_thickness) * web_thickness**3) / 3
        
        return {
            "area": area,
            "moment_of_inertia_y": iy,
            "moment_of_inertia_z": iz,
            "section_modulus_y": zy,
            "section_modulus_z": zz,
            "torsional_constant": j,
            "dimensions": {
                "depth": depth,
                "width": width,
                "web_thickness": web_thickness,
                "flange_thickness": flange_thickness
            }
        }
    
    @staticmethod
    def calculate_channel_properties(depth: float, width: float,
                                   web_thickness: float, flange_thickness: float) -> Dict[str, float]:
        """Calculate properties of channel section"""
        # Area
        area = 2 * width * flange_thickness + (depth - 2 * flange_thickness) * web_thickness
        
        # Moment of inertia about y-axis
        iy = (web_thickness * depth**3 + 2 * width * flange_thickness * (depth - flange_thickness)**2) / 12
        
        # Moment of inertia about z-axis
        iz = (2 * flange_thickness * width**3 + (depth - 2 * flange_thickness) * web_thickness**3) / 12
        
        # Section modulus
        zy = 2 * iy / depth
        zz = iz / (width - web_thickness/2)
        
        # Torsional constant (approximate)
        j = (2 * width * flange_thickness**3 + (depth - 2 * flange_thickness) * web_thickness**3) / 3
        
        return {
            "area": area,
            "moment_of_inertia_y": iy,
            "moment_of_inertia_z": iz,
            "section_modulus_y": zy,
            "section_modulus_z": zz,
            "torsional_constant": j,
            "dimensions": {
                "depth": depth,
                "width": width,
                "web_thickness": web_thickness,
                "flange_thickness": flange_thickness
            }
        }
    
    @staticmethod
    def calculate_circular_tube_properties(diameter: float, thickness: float) -> Dict[str, float]:
        """Calculate properties of circular hollow section"""
        outer_radius = diameter / 2
        inner_radius = outer_radius - thickness
        
        # Area
        area = math.pi * (outer_radius**2 - inner_radius**2)
        
        # Moment of inertia (same about both axes)
        i = math.pi * (outer_radius**4 - inner_radius**4) / 4
        
        # Section modulus
        z = i / outer_radius
        
        # Torsional constant
        j = 2 * i
        
        return {
            "area": area,
            "moment_of_inertia_y": i,
            "moment_of_inertia_z": i,
            "section_modulus_y": z,
            "section_modulus_z": z,
            "torsional_constant": j,
            "dimensions": {
                "diameter": diameter,
                "thickness": thickness
            }
        }
    
    @staticmethod
    def calculate_rectangular_tube_properties(height: float, width: float, thickness: float) -> Dict[str, float]:
        """Calculate properties of rectangular hollow section"""
        # Area
        area = height * width - (height - 2 * thickness) * (width - 2 * thickness)
        
        # Moment of inertia about y-axis (strong axis)
        iy = (width * height**3 - (width - 2 * thickness) * (height - 2 * thickness)**3) / 12
        
        # Moment of inertia about z-axis (weak axis)
        iz = (height * width**3 - (height - 2 * thickness) * (width - 2 * thickness)**3) / 12
        
        # Section modulus
        zy = 2 * iy / height
        zz = 2 * iz / width
        
        # Torsional constant (approximate)
        a = max(height, width) / 2 - thickness
        b = min(height, width) / 2 - thickness
        j = 4 * a * b * thickness * (a + b) / (a + b + 2 * thickness)
        
        return {
            "area": area,
            "moment_of_inertia_y": iy,
            "moment_of_inertia_z": iz,
            "section_modulus_y": zy,
            "section_modulus_z": zz,
            "torsional_constant": j,
            "dimensions": {
                "height": height,
                "width": width,
                "thickness": thickness
            }
        }
    
    @staticmethod
    def calculate_rectangle_properties(height: float, width: float) -> Dict[str, float]:
        """Calculate properties of solid rectangular section"""
        # Area
        area = height * width
        
        # Moment of inertia
        iy = width * height**3 / 12
        iz = height * width**3 / 12
        
        # Section modulus
        zy = 2 * iy / height
        zz = 2 * iz / width
        
        # Torsional constant
        if height >= width:
            j = width * height**3 * (16/3 - 3.36 * height/width * (1 - height**4/(12*width**4)))
        else:
            j = height * width**3 * (16/3 - 3.36 * width/height * (1 - width**4/(12*height**4)))
        
        return {
            "area": area,
            "moment_of_inertia_y": iy,
            "moment_of_inertia_z": iz,
            "section_modulus_y": zy,
            "section_modulus_z": zz,
            "torsional_constant": j,
            "dimensions": {
                "height": height,
                "width": width
            }
        }
    
    @staticmethod
    def calculate_circle_properties(diameter: float) -> Dict[str, float]:
        """Calculate properties of solid circular section"""
        radius = diameter / 2
        
        # Area
        area = math.pi * radius**2
        
        # Moment of inertia (same about both axes)
        i = math.pi * radius**4 / 4
        
        # Section modulus
        z = i / radius
        
        # Torsional constant
        j = 2 * i
        
        return {
            "area": area,
            "moment_of_inertia_y": i,
            "moment_of_inertia_z": i,
            "section_modulus_y": z,
            "section_modulus_z": z,
            "torsional_constant": j,
            "dimensions": {
                "diameter": diameter
            }
        }


class SectionManager:
    def __init__(self, db_session: Session, model_id: int):
        self.db = db_session
        self.model_id = model_id
        self._sections_cache = {}
        self._load_sections()
    
    def _load_sections(self):
        sections = self.db.query(Section).filter(Section.model_id == self.model_id).all()
        for section in sections:
            self._sections_cache[section.id] = section
    
    def create_section(self, name: str, section_type: SectionType,
                      area: float, moment_of_inertia_y: float, moment_of_inertia_z: float,
                      torsional_constant: float, section_modulus_y: float = None,
                      section_modulus_z: float = None, dimensions: Dict[str, Any] = None) -> Section:
        
        section = Section(
            model_id=self.model_id,
            name=name,
            section_type=section_type,
            area=area,
            moment_of_inertia_y=moment_of_inertia_y,
            moment_of_inertia_z=moment_of_inertia_z,
            torsional_constant=torsional_constant,
            section_modulus_y=section_modulus_y,
            section_modulus_z=section_modulus_z,
            dimensions=dimensions or {}
        )
        
        self.db.add(section)
        self.db.commit()
        self.db.refresh(section)
        
        self._sections_cache[section.id] = section
        return section
    
    def create_from_library(self, name: str, section_type: SectionType, designation: str) -> Section:
        """Create section from predefined library"""
        
        if section_type == SectionType.I_SECTION:
            library = SectionLibrary.get_steel_i_sections()
            if designation not in library:
                raise ValueError(f"I-section {designation} not found in library")
            
            dims = library[designation]
            props = SectionCalculator.calculate_i_section_properties(
                dims["depth"], dims["width"], dims["web_thickness"], dims["flange_thickness"]
            )
            
        elif section_type == SectionType.CHANNEL:
            library = SectionLibrary.get_steel_channels()
            if designation not in library:
                raise ValueError(f"Channel section {designation} not found in library")
            
            dims = library[designation]
            props = SectionCalculator.calculate_channel_properties(
                dims["depth"], dims["width"], dims["web_thickness"], dims["flange_thickness"]
            )
            
        elif section_type == SectionType.TUBE:
            library = SectionLibrary.get_steel_tubes()
            if designation not in library:
                raise ValueError(f"Tube section {designation} not found in library")
            
            dims = library[designation]
            if "diameter" in dims:
                props = SectionCalculator.calculate_circular_tube_properties(
                    dims["diameter"], dims["thickness"]
                )
            else:
                props = SectionCalculator.calculate_rectangular_tube_properties(
                    dims["height"], dims["width"], dims["thickness"]
                )
        else:
            raise ValueError(f"Section type {section_type} not supported in library")
        
        return self.create_section(
            name=name,
            section_type=section_type,
            area=props["area"],
            moment_of_inertia_y=props["moment_of_inertia_y"],
            moment_of_inertia_z=props["moment_of_inertia_z"],
            torsional_constant=props["torsional_constant"],
            section_modulus_y=props["section_modulus_y"],
            section_modulus_z=props["section_modulus_z"],
            dimensions=props["dimensions"]
        )
    
    def create_rectangular_section(self, name: str, height: float, width: float) -> Section:
        """Create rectangular section"""
        props = SectionCalculator.calculate_rectangle_properties(height, width)
        
        return self.create_section(
            name=name,
            section_type=SectionType.RECTANGLE,
            area=props["area"],
            moment_of_inertia_y=props["moment_of_inertia_y"],
            moment_of_inertia_z=props["moment_of_inertia_z"],
            torsional_constant=props["torsional_constant"],
            section_modulus_y=props["section_modulus_y"],
            section_modulus_z=props["section_modulus_z"],
            dimensions=props["dimensions"]
        )
    
    def create_circular_section(self, name: str, diameter: float) -> Section:
        """Create circular section"""
        props = SectionCalculator.calculate_circle_properties(diameter)
        
        return self.create_section(
            name=name,
            section_type=SectionType.CIRCLE,
            area=props["area"],
            moment_of_inertia_y=props["moment_of_inertia_y"],
            moment_of_inertia_z=props["moment_of_inertia_z"],
            torsional_constant=props["torsional_constant"],
            section_modulus_y=props["section_modulus_y"],
            section_modulus_z=props["section_modulus_z"],
            dimensions=props["dimensions"]
        )
    
    def get_section(self, section_id: int) -> Optional[Section]:
        return self._sections_cache.get(section_id)
    
    def get_section_by_name(self, name: str) -> Optional[Section]:
        for section in self._sections_cache.values():
            if section.name == name:
                return section
        return None
    
    def get_all_sections(self) -> List[Section]:
        return list(self._sections_cache.values())
    
    def get_sections_by_type(self, section_type: SectionType) -> List[Section]:
        return [sec for sec in self._sections_cache.values() if sec.section_type == section_type]
    
    def update_section_properties(self, section_id: int, properties: Dict[str, Any]) -> bool:
        section = self.get_section(section_id)
        if not section:
            return False
        
        for prop, value in properties.items():
            if hasattr(section, prop):
                setattr(section, prop, value)
        
        self.db.commit()
        return True
    
    def delete_section(self, section_id: int) -> bool:
        section = self.get_section(section_id)
        if not section:
            return False
        
        # Check if section is used by elements
        from db.models import Element
        elements_count = self.db.query(Element).filter(Element.section_id == section_id).count()
        
        if elements_count > 0:
            raise ValueError(f"Cannot delete section {section_id}: it is used by {elements_count} elements")
        
        self.db.delete(section)
        self.db.commit()
        
        if section_id in self._sections_cache:
            del self._sections_cache[section_id]
        
        return True
    
    def get_available_designations(self, section_type: SectionType) -> List[str]:
        """Get available section designations from library"""
        if section_type == SectionType.I_SECTION:
            return list(SectionLibrary.get_steel_i_sections().keys())
        elif section_type == SectionType.CHANNEL:
            return list(SectionLibrary.get_steel_channels().keys())
        elif section_type == SectionType.TUBE:
            return list(SectionLibrary.get_steel_tubes().keys())
        else:
            return []
    
    def get_section_properties(self, section_id: int) -> Optional[Dict[str, Any]]:
        """Get all section properties as dictionary"""
        section = self.get_section(section_id)
        if not section:
            return None
        
        return {
            "id": section.id,
            "name": section.name,
            "section_type": section.section_type,
            "area": section.area,
            "moment_of_inertia_y": section.moment_of_inertia_y,
            "moment_of_inertia_z": section.moment_of_inertia_z,
            "torsional_constant": section.torsional_constant,
            "section_modulus_y": section.section_modulus_y,
            "section_modulus_z": section.section_modulus_z,
            "dimensions": section.dimensions
        }
