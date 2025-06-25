from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import get_current_user
from api.projects import get_project_by_id

router = APIRouter(prefix="/api/projects", tags=["models"])

# Mock database for structural models
fake_models_db = {}
model_counter = 0

class ModelCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    units: Optional[str] = "m"

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    units: Optional[str] = None

class Node(BaseModel):
    id: int
    label: str
    position: List[float]  # [x, y, z]
    boundary_conditions: Optional[Dict[str, bool]] = None

class Element(BaseModel):
    id: int
    label: str
    type: str
    start_node: int
    end_node: int
    material_id: Optional[int] = None
    section_id: Optional[int] = None

class Material(BaseModel):
    id: int
    name: str
    type: str  # concrete, steel, etc.
    properties: Dict[str, float]

class StructuralModel(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    units: str
    created_at: datetime
    updated_at: datetime
    nodes: List[Node] = []
    elements: List[Element] = []
    materials: List[Material] = []

def create_model_in_db(project_id: int, model_data: ModelCreate, user_id: int):
    global model_counter
    model_counter += 1
    
    # Sample structural data
    sample_nodes = [
        {"id": 1, "label": "N1", "position": [0.0, 0.0, 0.0], "boundary_conditions": {"fx": True, "fy": True, "fz": True, "mx": True, "my": True, "mz": True}},
        {"id": 2, "label": "N2", "position": [5.0, 0.0, 0.0], "boundary_conditions": {"fx": False, "fy": True, "fz": True, "mx": False, "my": False, "mz": False}},
        {"id": 3, "label": "N3", "position": [10.0, 0.0, 0.0], "boundary_conditions": {"fx": True, "fy": True, "fz": True, "mx": True, "my": True, "mz": True}},
        {"id": 4, "label": "N4", "position": [0.0, 0.0, 3.0], "boundary_conditions": {"fx": False, "fy": False, "fz": False, "mx": False, "my": False, "mz": False}},
        {"id": 5, "label": "N5", "position": [5.0, 0.0, 3.0], "boundary_conditions": {"fx": False, "fy": False, "fz": False, "mx": False, "my": False, "mz": False}},
        {"id": 6, "label": "N6", "position": [10.0, 0.0, 3.0], "boundary_conditions": {"fx": False, "fy": False, "fz": False, "mx": False, "my": False, "mz": False}},
    ]
    
    sample_elements = [
        {"id": 1, "label": "E1", "type": "beam", "start_node": 1, "end_node": 2, "material_id": 1, "section_id": 1},
        {"id": 2, "label": "E2", "type": "beam", "start_node": 2, "end_node": 3, "material_id": 1, "section_id": 1},
        {"id": 3, "label": "E3", "type": "column", "start_node": 1, "end_node": 4, "material_id": 2, "section_id": 2},
        {"id": 4, "label": "E4", "type": "column", "start_node": 2, "end_node": 5, "material_id": 2, "section_id": 2},
        {"id": 5, "label": "E5", "type": "column", "start_node": 3, "end_node": 6, "material_id": 2, "section_id": 2},
        {"id": 6, "label": "E6", "type": "beam", "start_node": 4, "end_node": 5, "material_id": 1, "section_id": 1},
        {"id": 7, "label": "E7", "type": "beam", "start_node": 5, "end_node": 6, "material_id": 1, "section_id": 1},
    ]
    
    sample_materials = [
        {
            "id": 1,
            "name": "M25 Concrete",
            "type": "concrete",
            "properties": {
                "fck": 25.0,  # MPa
                "elastic_modulus": 25000.0,  # MPa
                "poisson_ratio": 0.2,
                "density": 25.0  # kN/m3
            }
        },
        {
            "id": 2,
            "name": "Fe415 Steel",
            "type": "steel",
            "properties": {
                "fy": 415.0,  # MPa
                "elastic_modulus": 200000.0,  # MPa
                "poisson_ratio": 0.3,
                "density": 78.5  # kN/m3
            }
        }
    ]
    
    model = {
        "id": model_counter,
        "project_id": project_id,
        "name": model_data.name,
        "description": model_data.description,
        "units": model_data.units,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "nodes": sample_nodes,
        "elements": sample_elements,
        "materials": sample_materials
    }
    
    if user_id not in fake_models_db:
        fake_models_db[user_id] = {}
    if project_id not in fake_models_db[user_id]:
        fake_models_db[user_id][project_id] = {}
    
    fake_models_db[user_id][project_id][model_counter] = model
    return model

def get_project_models(project_id: int, user_id: int):
    return list(fake_models_db.get(user_id, {}).get(project_id, {}).values())

def get_model_by_id(project_id: int, model_id: int, user_id: int):
    return fake_models_db.get(user_id, {}).get(project_id, {}).get(model_id)

def update_model_in_db(project_id: int, model_id: int, model_data: ModelUpdate, user_id: int):
    model = get_model_by_id(project_id, model_id, user_id)
    if not model:
        return None
    
    if model_data.name is not None:
        model["name"] = model_data.name
    if model_data.description is not None:
        model["description"] = model_data.description
    if model_data.units is not None:
        model["units"] = model_data.units
    
    model["updated_at"] = datetime.utcnow()
    return model

def delete_model_from_db(project_id: int, model_id: int, user_id: int):
    project_models = fake_models_db.get(user_id, {}).get(project_id, {})
    return project_models.pop(model_id, None) is not None

@router.post("/{project_id}/models", response_model=StructuralModel)
def create_model(
    project_id: int,
    model: ModelCreate,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    model_data = create_model_in_db(project_id, model, current_user["id"])
    return StructuralModel(**model_data)

@router.get("/{project_id}/models", response_model=List[StructuralModel])
def get_models(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    models = get_project_models(project_id, current_user["id"])
    return [StructuralModel(**model) for model in models]

@router.get("/{project_id}/models/{model_id}", response_model=StructuralModel)
def get_model(
    project_id: int,
    model_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return StructuralModel(**model)

@router.put("/{project_id}/models/{model_id}", response_model=StructuralModel)
def update_model(
    project_id: int,
    model_id: int,
    model: ModelUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    updated_model = update_model_in_db(project_id, model_id, model, current_user["id"])
    if not updated_model:
        raise HTTPException(status_code=404, detail="Model not found")
    return StructuralModel(**updated_model)

@router.delete("/{project_id}/models/{model_id}")
def delete_model(
    project_id: int,
    model_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not delete_model_from_db(project_id, model_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}
