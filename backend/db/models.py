from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class ElementType(str, enum.Enum):
    BEAM = "beam"
    COLUMN = "column"
    BRACE = "brace"
    SHELL = "shell"
    PLATE = "plate"
    WALL = "wall"
    SLAB = "slab"


class MaterialType(str, enum.Enum):
    CONCRETE = "concrete"
    STEEL = "steel"
    TIMBER = "timber"
    COMPOSITE = "composite"


class SectionType(str, enum.Enum):
    I_SECTION = "i_section"
    CHANNEL = "channel"
    TUBE = "tube"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    CUSTOM = "custom"


class LoadType(str, enum.Enum):
    POINT = "point"
    DISTRIBUTED = "distributed"
    AREA = "area"
    WIND = "wind"
    SEISMIC = "seismic"


class SupportType(str, enum.Enum):
    FIXED = "fixed"
    PINNED = "pinned"
    ROLLER = "roller"
    FREE = "free"


# Users and Organizations (Multi-tenant SaaS)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ENGINEER)
    is_active = Column(Boolean, default=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    organization = relationship("Organization", back_populates="users")
    projects = relationship("Project", back_populates="owner")


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    users = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization")


# Projects and Models
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="projects")
    organization = relationship("Organization", back_populates="projects")
    models = relationship("Model", back_populates="project")


class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    units = Column(String, default="metric")  # metric, imperial
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", back_populates="models")
    nodes = relationship("Node", back_populates="model")
    elements = relationship("Element", back_populates="model")
    materials = relationship("Material", back_populates="model")
    sections = relationship("Section", back_populates="model")
    loads = relationship("Load", back_populates="model")
    load_combinations = relationship("LoadCombination", back_populates="model")
    boundary_conditions = relationship("BoundaryCondition", back_populates="model")
    analysis_results = relationship("AnalysisResult", back_populates="model")


# Structural Elements
class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    label = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    
    model = relationship("Model", back_populates="nodes")
    elements_start = relationship("Element", foreign_keys="Element.start_node_id", back_populates="start_node")
    elements_end = relationship("Element", foreign_keys="Element.end_node_id", back_populates="end_node")
    boundary_conditions = relationship("BoundaryCondition", back_populates="node")
    
    __table_args__ = (
        UniqueConstraint('model_id', 'label', name='_model_node_label_uc'),
        Index('ix_nodes_model_coordinates', 'model_id', 'x', 'y', 'z'),
    )


class Element(Base):
    __tablename__ = "elements"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    label = Column(String, nullable=False)
    element_type = Column(Enum(ElementType), nullable=False)
    start_node_id = Column(Integer, ForeignKey("nodes.id"))
    end_node_id = Column(Integer, ForeignKey("nodes.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    orientation_angle = Column(Float, default=0.0)
    releases = Column(JSON)  # Store releases as JSON
    
    model = relationship("Model", back_populates="elements")
    start_node = relationship("Node", foreign_keys=[start_node_id], back_populates="elements_start")
    end_node = relationship("Node", foreign_keys=[end_node_id], back_populates="elements_end")
    material = relationship("Material", back_populates="elements")
    section = relationship("Section", back_populates="elements")
    loads = relationship("Load", back_populates="element")
    
    __table_args__ = (
        UniqueConstraint('model_id', 'label', name='_model_element_label_uc'),
        Index('ix_elements_model_type', 'model_id', 'element_type'),
    )


class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    name = Column(String, nullable=False)
    material_type = Column(Enum(MaterialType), nullable=False)
    
    # Mechanical properties
    elastic_modulus = Column(Float, nullable=False)
    poisson_ratio = Column(Float, nullable=False)
    density = Column(Float, nullable=False)
    thermal_expansion = Column(Float)
    
    # Strength properties
    yield_strength = Column(Float)
    ultimate_strength = Column(Float)
    compressive_strength = Column(Float)
    
    # Code-specific properties
    design_code = Column(String)  # IS456, ACI318, EC2, etc.
    grade = Column(String)  # M25, Grade60, etc.
    
    model = relationship("Model", back_populates="materials")
    elements = relationship("Element", back_populates="material")
    
    __table_args__ = (
        UniqueConstraint('model_id', 'name', name='_model_material_name_uc'),
    )


class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    name = Column(String, nullable=False)
    section_type = Column(Enum(SectionType), nullable=False)
    
    # Geometric properties
    area = Column(Float, nullable=False)
    moment_of_inertia_y = Column(Float, nullable=False)
    moment_of_inertia_z = Column(Float, nullable=False)
    torsional_constant = Column(Float, nullable=False)
    section_modulus_y = Column(Float)
    section_modulus_z = Column(Float)
    
    # Dimensions (varies by section type)
    dimensions = Column(JSON)  # Store dimensions as JSON
    
    model = relationship("Model", back_populates="sections")
    elements = relationship("Element", back_populates="section")
    
    __table_args__ = (
        UniqueConstraint('model_id', 'name', name='_model_section_name_uc'),
    )


# Loads and Load Combinations
class Load(Base):
    __tablename__ = "loads"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    name = Column(String, nullable=False)
    load_type = Column(Enum(LoadType), nullable=False)
    load_case = Column(String, nullable=False)  # DL, LL, WL, EL, etc.
    
    # Load application
    element_id = Column(Integer, ForeignKey("elements.id"), nullable=True)  # For element loads
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)  # For point loads
    
    # Load values
    force_x = Column(Float, default=0.0)
    force_y = Column(Float, default=0.0)
    force_z = Column(Float, default=0.0)
    moment_x = Column(Float, default=0.0)
    moment_y = Column(Float, default=0.0)
    moment_z = Column(Float, default=0.0)
    
    # Distributed load parameters
    start_distance = Column(Float)  # Distance from start of element
    end_distance = Column(Float)  # Distance from start of element
    
    model = relationship("Model", back_populates="loads")
    element = relationship("Element", back_populates="loads")
    node = relationship("Node")


class LoadCombination(Base):
    __tablename__ = "load_combinations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    name = Column(String, nullable=False)
    combination_type = Column(String)  # ULS, SLS, etc.
    factors = Column(JSON)  # Load case factors as JSON
    
    model = relationship("Model", back_populates="load_combinations")
    
    __table_args__ = (
        UniqueConstraint('model_id', 'name', name='_model_loadcomb_name_uc'),
    )


class BoundaryCondition(Base):
    __tablename__ = "boundary_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    node_id = Column(Integer, ForeignKey("nodes.id"))
    support_type = Column(Enum(SupportType), nullable=False)
    
    # Translational restraints
    restrain_x = Column(Boolean, default=False)
    restrain_y = Column(Boolean, default=False)
    restrain_z = Column(Boolean, default=False)
    
    # Rotational restraints
    restrain_rx = Column(Boolean, default=False)
    restrain_ry = Column(Boolean, default=False)
    restrain_rz = Column(Boolean, default=False)
    
    # Spring constants (for elastic supports)
    spring_kx = Column(Float)
    spring_ky = Column(Float)
    spring_kz = Column(Float)
    spring_krx = Column(Float)
    spring_kry = Column(Float)
    spring_krz = Column(Float)
    
    model = relationship("Model", back_populates="boundary_conditions")
    node = relationship("Node", back_populates="boundary_conditions")


# Analysis Results
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    analysis_type = Column(String, nullable=False)  # static, modal, response_spectrum, etc.
    load_combination = Column(String)
    status = Column(String)  # running, completed, failed
    
    # Result data stored as JSON
    node_displacements = Column(JSON)
    element_forces = Column(JSON)
    element_stresses = Column(JSON)
    reaction_forces = Column(JSON)
    mode_shapes = Column(JSON)  # For modal analysis
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    model = relationship("Model", back_populates="analysis_results")


# Design Results
class DesignResult(Base):
    __tablename__ = "design_results"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    element_id = Column(Integer, ForeignKey("elements.id"))
    design_code = Column(String, nullable=False)
    design_type = Column(String, nullable=False)  # flexure, shear, axial, etc.
    
    # Design ratios and checks
    utilization_ratio = Column(Float)
    design_passed = Column(Boolean)
    
    # Design data as JSON
    design_data = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    model = relationship("Model")
    element = relationship("Element")


# Reinforcement Details
class ReinforcementDetail(Base):
    __tablename__ = "reinforcement_details"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    element_id = Column(Integer, ForeignKey("elements.id"))
    
    # Longitudinal reinforcement
    top_rebar_size = Column(String)
    top_rebar_count = Column(Integer)
    bottom_rebar_size = Column(String)
    bottom_rebar_count = Column(Integer)
    
    # Transverse reinforcement
    stirrup_size = Column(String)
    stirrup_spacing = Column(Float)
    stirrup_legs = Column(Integer)
    
    # Cover and lengths
    cover = Column(Float)
    development_length = Column(Float)
    
    # Bar schedule data
    bar_schedule = Column(JSON)
    
    model = relationship("Model")
    element = relationship("Element")


# Connection Details
class ConnectionDetail(Base):
    __tablename__ = "connection_details"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    connection_type = Column(String, nullable=False)  # bolted, welded, etc.
    
    # Connected elements
    element1_id = Column(Integer, ForeignKey("elements.id"))
    element2_id = Column(Integer, ForeignKey("elements.id"))
    
    # Connection geometry and details
    connection_data = Column(JSON)
    
    model = relationship("Model")
    element1 = relationship("Element", foreign_keys=[element1_id])
    element2 = relationship("Element", foreign_keys=[element2_id])


# BIM Data Storage
class BIMData(Base):
    __tablename__ = "bim_data"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    file_format = Column(String, nullable=False)  # ifc, gltf, dxf
    file_path = Column(String)
    file_size = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    model = relationship("Model")
