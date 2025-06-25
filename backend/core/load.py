from typing import List, Optional, Dict, Any, Tuple
import math
from backend.db.models import Load, LoadType, LoadCombination, Element, Node
from sqlalchemy.orm import Session


class LoadGenerator:
    """Generate loads based on codes and standards"""
    
    @staticmethod
    def generate_wind_loads(building_height: float, building_width: float, building_length: float,
                          wind_speed: float, terrain_category: str = "II", 
                          importance_factor: float = 1.0, code: str = "IS875") -> Dict[str, Any]:
        """Generate wind loads based on building geometry and code"""
        
        if code == "IS875":
            # IS 875 (Part 3) Wind Loads
            
            # Basic wind speed factors
            terrain_factors = {
                "I": {"k1": 1.0, "k3": 1.0},    # Open terrain
                "II": {"k1": 1.0, "k3": 1.0},   # Open terrain with scattered obstructions
                "III": {"k1": 0.91, "k3": 1.0}, # Terrain with numerous obstructions
                "IV": {"k1": 0.71, "k3": 1.0}   # Terrain with large and numerous obstructions
            }
            
            k1 = terrain_factors.get(terrain_category, {"k1": 1.0})["k1"]
            k2 = importance_factor
            k3 = 1.0  # Topography factor (assumed flat terrain)
            k4 = 1.0  # Risk coefficient
            
            # Design wind speed
            vz = wind_speed * math.sqrt(k1 * k2 * k3 * k4)
            
            # Design wind pressure
            pz = 0.6 * (vz ** 2) / 1000  # kN/m² (converted from N/m²)
            
            # Pressure coefficients (simplified)
            cpe_windward = 0.8
            cpe_leeward = -0.5
            cpe_side = -0.7
            
            return {
                "design_wind_speed": vz,
                "design_wind_pressure": pz,
                "windward_pressure": pz * cpe_windward,
                "leeward_pressure": pz * cpe_leeward,
                "side_pressure": pz * cpe_side,
                "height_variation": True,
                "code": code
            }
        
        elif code == "ASCE7":
            # ASCE 7 Wind Loads
            
            # Exposure categories
            exposure_factors = {
                "B": {"alpha": 7.0, "zg": 365.76},   # Urban and suburban areas
                "C": {"alpha": 9.5, "zg": 274.32},   # Open terrain
                "D": {"alpha": 11.5, "zg": 213.36}   # Flat, unobstructed areas
            }
            
            exposure = exposure_factors.get(terrain_category, exposure_factors["C"])
            
            # Velocity pressure coefficient
            kz = 2.01 * (building_height / exposure["zg"]) ** (2/exposure["alpha"])
            if kz < 0.85:
                kz = 0.85
            
            # Velocity pressure
            qz = 0.613 * kz * (wind_speed ** 2) * importance_factor  # N/m²
            qz = qz / 1000  # Convert to kN/m²
            
            # External pressure coefficients (simplified)
            cp_windward = 0.8
            cp_leeward = -0.5
            cp_side = -0.7
            
            return {
                "design_wind_speed": wind_speed,
                "velocity_pressure": qz,
                "windward_pressure": qz * cp_windward,
                "leeward_pressure": qz * cp_leeward,
                "side_pressure": qz * cp_side,
                "height_variation": True,
                "code": code
            }
        
        else:
            raise ValueError(f"Wind load code {code} not implemented")
    
    @staticmethod
    def generate_seismic_loads(building_mass: float, building_height: float,
                             seismic_zone: str, soil_type: str = "II",
                             importance_factor: float = 1.5, code: str = "IS1893") -> Dict[str, Any]:
        """Generate seismic loads based on building parameters and code"""
        
        if code == "IS1893":
            # IS 1893 Seismic Loads
            
            # Zone factors
            zone_factors = {
                "II": 0.10,
                "III": 0.16,
                "IV": 0.24,
                "V": 0.36
            }
            
            z = zone_factors.get(seismic_zone, 0.16)
            
            # Response reduction factor (assumed for RC frame)
            r = 3.0
            
            # Soil type factors
            soil_factors = {
                "I": {"sa_t0": 1.0, "sa_ts": 1.0},    # Hard soil/rock
                "II": {"sa_t0": 1.0, "sa_ts": 1.0},   # Medium soil
                "III": {"sa_t0": 1.0, "sa_ts": 1.0}   # Soft soil
            }
            
            # Calculate fundamental period (approximate)
            t = 0.075 * (building_height ** 0.75)  # For RC frame buildings
            
            # Design horizontal acceleration spectrum
            if t <= 0.1:
                sa_g = 1 + 15 * t
            elif t <= 0.4:
                sa_g = 2.5
            elif t <= 4.0:
                sa_g = 1.0 / t
            else:
                sa_g = 0.25
            
            # Design horizontal seismic coefficient
            ah = (z * importance_factor * sa_g) / (2 * r)
            
            # Base shear
            vb = ah * building_mass
            
            return {
                "zone_factor": z,
                "importance_factor": importance_factor,
                "response_reduction_factor": r,
                "fundamental_period": t,
                "design_acceleration_coefficient": ah,
                "base_shear": vb,
                "code": code
            }
        
        elif code == "ASCE7":
            # ASCE 7 Seismic Loads
            
            # Site class factors (simplified)
            site_factors = {
                "A": {"fa": 0.8, "fv": 0.8},    # Hard rock
                "B": {"fa": 1.0, "fv": 1.0},    # Rock
                "C": {"fa": 1.2, "fv": 1.8},    # Very dense soil
                "D": {"fa": 1.6, "fv": 2.4},    # Stiff soil
                "E": {"fa": 2.5, "fv": 3.5}     # Soft clay soil
            }
            
            # Seismic design parameters (simplified - would need actual maps)
            ss = 1.5  # Mapped spectral acceleration (short periods)
            s1 = 0.6  # Mapped spectral acceleration (1 second period)
            
            fa = site_factors.get(soil_type, {"fa": 1.0})["fa"]
            fv = site_factors.get(soil_type, {"fv": 1.0})["fv"]
            
            sms = fa * ss
            sm1 = fv * s1
            
            sds = (2/3) * sms
            sd1 = (2/3) * sm1
            
            # Calculate fundamental period
            ct = 0.028  # For steel moment frame
            x = 0.8
            t = ct * (building_height ** x)
            
            # Response modification coefficient (assumed for steel frame)
            r = 8.0
            
            # Seismic response coefficient
            cs = sds / (r / importance_factor)
            
            # Base shear
            v = cs * building_mass
            
            return {
                "site_modified_acceleration_sms": sms,
                "site_modified_acceleration_sm1": sm1,
                "design_acceleration_sds": sds,
                "design_acceleration_sd1": sd1,
                "fundamental_period": t,
                "response_modification_factor": r,
                "seismic_response_coefficient": cs,
                "base_shear": v,
                "code": code
            }
        
        else:
            raise ValueError(f"Seismic load code {code} not implemented")
    
    @staticmethod
    def generate_load_combinations(code: str = "IS1893") -> List[Dict[str, Any]]:
        """Generate load combinations based on design code"""
        
        if code == "IS1893":
            # IS 1893 Load Combinations
            return [
                {"name": "DL", "type": "SLS", "factors": {"DL": 1.0}},
                {"name": "DL+LL", "type": "SLS", "factors": {"DL": 1.0, "LL": 1.0}},
                {"name": "1.5(DL+LL)", "type": "ULS", "factors": {"DL": 1.5, "LL": 1.5}},
                {"name": "1.2(DL+LL+WL)", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.2, "WL": 1.2}},
                {"name": "1.5(DL+WL)", "type": "ULS", "factors": {"DL": 1.5, "WL": 1.5}},
                {"name": "0.9DL+1.5WL", "type": "ULS", "factors": {"DL": 0.9, "WL": 1.5}},
                {"name": "1.2(DL+LL+EL)", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.2, "EL": 1.2}},
                {"name": "1.5(DL+EL)", "type": "ULS", "factors": {"DL": 1.5, "EL": 1.5}},
                {"name": "0.9DL+1.5EL", "type": "ULS", "factors": {"DL": 0.9, "EL": 1.5}},
            ]
        
        elif code == "ACI318":
            # ACI 318 Load Combinations
            return [
                {"name": "1.4D", "type": "ULS", "factors": {"DL": 1.4}},
                {"name": "1.2D+1.6L", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.6}},
                {"name": "1.2D+1.0L+1.0W", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.0, "WL": 1.0}},
                {"name": "1.2D+1.0L-1.0W", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.0, "WL": -1.0}},
                {"name": "1.2D+1.0L+1.0E", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.0, "EL": 1.0}},
                {"name": "1.2D+1.0L-1.0E", "type": "ULS", "factors": {"DL": 1.2, "LL": 1.0, "EL": -1.0}},
                {"name": "0.9D+1.0W", "type": "ULS", "factors": {"DL": 0.9, "WL": 1.0}},
                {"name": "0.9D-1.0W", "type": "ULS", "factors": {"DL": 0.9, "WL": -1.0}},
                {"name": "0.9D+1.0E", "type": "ULS", "factors": {"DL": 0.9, "EL": 1.0}},
                {"name": "0.9D-1.0E", "type": "ULS", "factors": {"DL": 0.9, "EL": -1.0}},
            ]
        
        elif code == "EC2":
            # Eurocode Load Combinations
            return [
                {"name": "1.35G", "type": "ULS", "factors": {"DL": 1.35}},
                {"name": "1.35G+1.5Q", "type": "ULS", "factors": {"DL": 1.35, "LL": 1.5}},
                {"name": "1.35G+1.5W", "type": "ULS", "factors": {"DL": 1.35, "WL": 1.5}},
                {"name": "1.0G+1.5W", "type": "ULS", "factors": {"DL": 1.0, "WL": 1.5}},
                {"name": "1.35G+1.5Q+0.9W", "type": "ULS", "factors": {"DL": 1.35, "LL": 1.5, "WL": 0.9}},
                {"name": "1.35G+0.9Q+1.5W", "type": "ULS", "factors": {"DL": 1.35, "LL": 0.9, "WL": 1.5}},
                {"name": "1.0G+1.0Q", "type": "SLS", "factors": {"DL": 1.0, "LL": 1.0}},
                {"name": "1.0G+0.9Q", "type": "SLS", "factors": {"DL": 1.0, "LL": 0.9}},
            ]
        
        else:
            raise ValueError(f"Load combination code {code} not implemented")


class LoadManager:
    def __init__(self, db_session: Session, model_id: int):
        self.db = db_session
        self.model_id = model_id
        self._loads_cache = {}
        self._load_combinations_cache = {}
        self._load_loads()
        self._load_load_combinations()
    
    def _load_loads(self):
        loads = self.db.query(Load).filter(Load.model_id == self.model_id).all()
        for load in loads:
            self._loads_cache[load.id] = load
    
    def _load_load_combinations(self):
        combinations = self.db.query(LoadCombination).filter(LoadCombination.model_id == self.model_id).all()
        for combination in combinations:
            self._load_combinations_cache[combination.id] = combination
    
    def create_point_load(self, name: str, load_case: str, node_id: int,
                         force_x: float = 0.0, force_y: float = 0.0, force_z: float = 0.0,
                         moment_x: float = 0.0, moment_y: float = 0.0, moment_z: float = 0.0) -> Load:
        """Create point load at node"""
        
        # Validate node exists
        node = self.db.query(Node).filter(Node.id == node_id).first()
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        load = Load(
            model_id=self.model_id,
            name=name,
            load_type=LoadType.POINT,
            load_case=load_case,
            node_id=node_id,
            force_x=force_x,
            force_y=force_y,
            force_z=force_z,
            moment_x=moment_x,
            moment_y=moment_y,
            moment_z=moment_z
        )
        
        self.db.add(load)
        self.db.commit()
        self.db.refresh(load)
        
        self._loads_cache[load.id] = load
        return load
    
    def create_distributed_load(self, name: str, load_case: str, element_id: int,
                              force_x: float = 0.0, force_y: float = 0.0, force_z: float = 0.0,
                              start_distance: float = 0.0, end_distance: float = None) -> Load:
        """Create distributed load on element"""
        
        # Validate element exists
        element = self.db.query(Element).filter(Element.id == element_id).first()
        if not element:
            raise ValueError(f"Element {element_id} not found")
        
        # If end_distance not specified, load is applied over entire element
        if end_distance is None:
            # Calculate element length
            start_node = element.start_node
            end_node = element.end_node
            length = math.sqrt(
                (end_node.x - start_node.x)**2 + 
                (end_node.y - start_node.y)**2 + 
                (end_node.z - start_node.z)**2
            )
            end_distance = length
        
        load = Load(
            model_id=self.model_id,
            name=name,
            load_type=LoadType.DISTRIBUTED,
            load_case=load_case,
            element_id=element_id,
            force_x=force_x,
            force_y=force_y,
            force_z=force_z,
            start_distance=start_distance,
            end_distance=end_distance
        )
        
        self.db.add(load)
        self.db.commit()
        self.db.refresh(load)
        
        self._loads_cache[load.id] = load
        return load
    
    def create_wind_loads(self, building_height: float, building_width: float, building_length: float,
                         wind_speed: float, terrain_category: str = "II", 
                         importance_factor: float = 1.0, code: str = "IS875") -> List[Load]:
        """Create wind loads on building"""
        
        wind_data = LoadGenerator.generate_wind_loads(
            building_height, building_width, building_length, wind_speed,
            terrain_category, importance_factor, code
        )
        
        loads = []
        
        # Create wind loads for different faces
        # This is a simplified implementation - would need actual building geometry
        
        # Windward face
        windward_load = Load(
            model_id=self.model_id,
            name=f"Wind_Windward_{code}",
            load_type=LoadType.WIND,
            load_case="WL",
            force_x=wind_data["windward_pressure"] * building_height * building_width,
            force_y=0.0,
            force_z=0.0
        )
        
        # Leeward face
        leeward_load = Load(
            model_id=self.model_id,
            name=f"Wind_Leeward_{code}",
            load_type=LoadType.WIND,
            load_case="WL",
            force_x=wind_data["leeward_pressure"] * building_height * building_width,
            force_y=0.0,
            force_z=0.0
        )
        
        # Side faces
        side_load1 = Load(
            model_id=self.model_id,
            name=f"Wind_Side1_{code}",
            load_type=LoadType.WIND,
            load_case="WL",
            force_x=0.0,
            force_y=wind_data["side_pressure"] * building_height * building_length,
            force_z=0.0
        )
        
        side_load2 = Load(
            model_id=self.model_id,
            name=f"Wind_Side2_{code}",
            load_type=LoadType.WIND,
            load_case="WL",
            force_x=0.0,
            force_y=-wind_data["side_pressure"] * building_height * building_length,
            force_z=0.0
        )
        
        for load in [windward_load, leeward_load, side_load1, side_load2]:
            self.db.add(load)
            loads.append(load)
        
        self.db.commit()
        
        for load in loads:
            self.db.refresh(load)
            self._loads_cache[load.id] = load
        
        return loads
    
    def create_seismic_loads(self, building_mass: float, building_height: float,
                           seismic_zone: str, soil_type: str = "II",
                           importance_factor: float = 1.5, code: str = "IS1893") -> List[Load]:
        """Create seismic loads on building"""
        
        seismic_data = LoadGenerator.generate_seismic_loads(
            building_mass, building_height, seismic_zone, soil_type,
            importance_factor, code
        )
        
        loads = []
        
        # Create seismic loads in X and Y directions
        seismic_x = Load(
            model_id=self.model_id,
            name=f"Seismic_X_{code}",
            load_type=LoadType.SEISMIC,
            load_case="EL",
            force_x=seismic_data["base_shear"],
            force_y=0.0,
            force_z=0.0
        )
        
        seismic_y = Load(
            model_id=self.model_id,
            name=f"Seismic_Y_{code}",
            load_type=LoadType.SEISMIC,
            load_case="EL",
            force_x=0.0,
            force_y=seismic_data["base_shear"],
            force_z=0.0
        )
        
        for load in [seismic_x, seismic_y]:
            self.db.add(load)
            loads.append(load)
        
        self.db.commit()
        
        for load in loads:
            self.db.refresh(load)
            self._loads_cache[load.id] = load
        
        return loads
    
    def create_load_combination(self, name: str, combination_type: str, factors: Dict[str, float]) -> LoadCombination:
        """Create load combination"""
        
        combination = LoadCombination(
            model_id=self.model_id,
            name=name,
            combination_type=combination_type,
            factors=factors
        )
        
        self.db.add(combination)
        self.db.commit()
        self.db.refresh(combination)
        
        self._load_combinations_cache[combination.id] = combination
        return combination
    
    def create_code_load_combinations(self, code: str = "IS1893") -> List[LoadCombination]:
        """Create standard load combinations based on code"""
        
        combinations_data = LoadGenerator.generate_load_combinations(code)
        combinations = []
        
        for combo_data in combinations_data:
            combination = self.create_load_combination(
                combo_data["name"],
                combo_data["type"],
                combo_data["factors"]
            )
            combinations.append(combination)
        
        return combinations
    
    def get_load(self, load_id: int) -> Optional[Load]:
        return self._loads_cache.get(load_id)
    
    def get_load_by_name(self, name: str) -> Optional[Load]:
        for load in self._loads_cache.values():
            if load.name == name:
                return load
        return None
    
    def get_all_loads(self) -> List[Load]:
        return list(self._loads_cache.values())
    
    def get_loads_by_case(self, load_case: str) -> List[Load]:
        return [load for load in self._loads_cache.values() if load.load_case == load_case]
    
    def get_loads_by_type(self, load_type: LoadType) -> List[Load]:
        return [load for load in self._loads_cache.values() if load.load_type == load_type]
    
    def get_element_loads(self, element_id: int) -> List[Load]:
        return [load for load in self._loads_cache.values() if load.element_id == element_id]
    
    def get_node_loads(self, node_id: int) -> List[Load]:
        return [load for load in self._loads_cache.values() if load.node_id == node_id]
    
    def get_load_combination(self, combination_id: int) -> Optional[LoadCombination]:
        return self._load_combinations_cache.get(combination_id)
    
    def get_all_load_combinations(self) -> List[LoadCombination]:
        return list(self._load_combinations_cache.values())
    
    def update_load(self, load_id: int, properties: Dict[str, Any]) -> bool:
        load = self.get_load(load_id)
        if not load:
            return False
        
        for prop, value in properties.items():
            if hasattr(load, prop):
                setattr(load, prop, value)
        
        self.db.commit()
        return True
    
    def delete_load(self, load_id: int) -> bool:
        load = self.get_load(load_id)
        if not load:
            return False
        
        self.db.delete(load)
        self.db.commit()
        
        if load_id in self._loads_cache:
            del self._loads_cache[load_id]
        
        return True
    
    def delete_load_combination(self, combination_id: int) -> bool:
        combination = self.get_load_combination(combination_id)
        if not combination:
            return False
        
        self.db.delete(combination)
        self.db.commit()
        
        if combination_id in self._load_combinations_cache:
            del self._load_combinations_cache[combination_id]
        
        return True
    
    def get_total_load_for_combination(self, combination_name: str) -> Dict[str, float]:
        """Calculate total loads for a given combination"""
        
        combination = None
        for combo in self._load_combinations_cache.values():
            if combo.name == combination_name:
                combination = combo
                break
        
        if not combination:
            return {}
        
        total_loads = {
            "force_x": 0.0,
            "force_y": 0.0,
            "force_z": 0.0,
            "moment_x": 0.0,
            "moment_y": 0.0,
            "moment_z": 0.0
        }
        
        # Apply factors to each load case
        for load_case, factor in combination.factors.items():
            case_loads = self.get_loads_by_case(load_case)
            
            for load in case_loads:
                total_loads["force_x"] += factor * load.force_x
                total_loads["force_y"] += factor * load.force_y
                total_loads["force_z"] += factor * load.force_z
                total_loads["moment_x"] += factor * load.moment_x
                total_loads["moment_y"] += factor * load.moment_y
                total_loads["moment_z"] += factor * load.moment_z
        
        return total_loads
