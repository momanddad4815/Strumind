from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import get_current_user
from api.models import get_model_by_id

router = APIRouter(prefix="/api/projects", tags=["elements"])

class ElementCreate(BaseModel):
    label: str
    type: str  # beam, column, brace, etc.
    start_node: int
    end_node: int
    material_id: Optional[int] = None
    section_id: Optional[int] = None

class ElementUpdate(BaseModel):
    label: Optional[str] = None
    type: Optional[str] = None
    start_node: Optional[int] = None
    end_node: Optional[int] = None
    material_id: Optional[int] = None
    section_id: Optional[int] = None

@router.post("/{project_id}/models/{model_id}/elements")
def create_element(
    project_id: int,
    model_id: int,
    element: ElementCreate,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Verify that the nodes exist
    start_node = next((n for n in model["nodes"] if n["id"] == element.start_node), None)
    if not start_node:
        raise HTTPException(status_code=404, detail=f"Start node with ID {element.start_node} not found")
    
    end_node = next((n for n in model["nodes"] if n["id"] == element.end_node), None)
    if not end_node:
        raise HTTPException(status_code=404, detail=f"End node with ID {element.end_node} not found")
    
    # Generate a new element ID
    new_element_id = 1
    if model["elements"]:
        new_element_id = max(e["id"] for e in model["elements"]) + 1
    
    # Create the new element
    new_element = {
        "id": new_element_id,
        "label": element.label,
        "type": element.type,
        "start_node": element.start_node,
        "end_node": element.end_node,
        "material_id": element.material_id,
        "section_id": element.section_id
    }
    
    # Add the element to the model
    model["elements"].append(new_element)
    
    return new_element

@router.get("/{project_id}/models/{model_id}/elements")
def get_elements(
    project_id: int,
    model_id: int,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model["elements"]

@router.get("/{project_id}/models/{model_id}/elements/{element_id}")
def get_element(
    project_id: int,
    model_id: int,
    element_id: int,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    element = next((e for e in model["elements"] if e["id"] == element_id), None)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    
    return element

@router.put("/{project_id}/models/{model_id}/elements/{element_id}")
def update_element(
    project_id: int,
    model_id: int,
    element_id: int,
    element_update: ElementUpdate,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    element_index = next((i for i, e in enumerate(model["elements"]) if e["id"] == element_id), None)
    if element_index is None:
        raise HTTPException(status_code=404, detail="Element not found")
    
    # Verify nodes if they're being updated
    if element_update.start_node is not None:
        start_node = next((n for n in model["nodes"] if n["id"] == element_update.start_node), None)
        if not start_node:
            raise HTTPException(status_code=404, detail=f"Start node with ID {element_update.start_node} not found")
    
    if element_update.end_node is not None:
        end_node = next((n for n in model["nodes"] if n["id"] == element_update.end_node), None)
        if not end_node:
            raise HTTPException(status_code=404, detail=f"End node with ID {element_update.end_node} not found")
    
    # Update the element
    if element_update.label is not None:
        model["elements"][element_index]["label"] = element_update.label
    if element_update.type is not None:
        model["elements"][element_index]["type"] = element_update.type
    if element_update.start_node is not None:
        model["elements"][element_index]["start_node"] = element_update.start_node
    if element_update.end_node is not None:
        model["elements"][element_index]["end_node"] = element_update.end_node
    if element_update.material_id is not None:
        model["elements"][element_index]["material_id"] = element_update.material_id
    if element_update.section_id is not None:
        model["elements"][element_index]["section_id"] = element_update.section_id
    
    return model["elements"][element_index]

@router.delete("/{project_id}/models/{model_id}/elements/{element_id}")
def delete_element(
    project_id: int,
    model_id: int,
    element_id: int,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Check if element exists
    element = next((e for e in model["elements"] if e["id"] == element_id), None)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    
    # Remove the element
    model["elements"] = [e for e in model["elements"] if e["id"] != element_id]
    
    return {"message": "Element deleted successfully"}