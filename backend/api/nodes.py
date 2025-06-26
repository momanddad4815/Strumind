from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import get_current_user
from api.models import get_model_by_id

router = APIRouter(prefix="/api/projects", tags=["nodes"])

class NodeCreate(BaseModel):
    label: str
    position: List[float]  # [x, y, z]
    boundary_conditions: Optional[Dict[str, bool]] = None

class NodeUpdate(BaseModel):
    label: Optional[str] = None
    position: Optional[List[float]] = None
    boundary_conditions: Optional[Dict[str, bool]] = None

@router.post("/{project_id}/models/{model_id}/nodes")
def create_node(
    project_id: int,
    model_id: int,
    node: NodeCreate,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Generate a new node ID
    new_node_id = 1
    if model["nodes"]:
        new_node_id = max(n["id"] for n in model["nodes"]) + 1
    
    # Create the new node
    new_node = {
        "id": new_node_id,
        "label": node.label,
        "position": node.position,
        "boundary_conditions": node.boundary_conditions or {
            "fx": False, "fy": False, "fz": False,
            "mx": False, "my": False, "mz": False
        }
    }
    
    # Add the node to the model
    model["nodes"].append(new_node)
    
    return new_node

@router.get("/{project_id}/models/{model_id}/nodes")
def get_nodes(
    project_id: int,
    model_id: int,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model["nodes"]

@router.get("/{project_id}/models/{model_id}/nodes/{node_id}")
def get_node(
    project_id: int,
    model_id: int,
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    node = next((n for n in model["nodes"] if n["id"] == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return node

@router.put("/{project_id}/models/{model_id}/nodes/{node_id}")
def update_node(
    project_id: int,
    model_id: int,
    node_id: int,
    node_update: NodeUpdate,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    node_index = next((i for i, n in enumerate(model["nodes"]) if n["id"] == node_id), None)
    if node_index is None:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Update the node
    if node_update.label is not None:
        model["nodes"][node_index]["label"] = node_update.label
    if node_update.position is not None:
        model["nodes"][node_index]["position"] = node_update.position
    if node_update.boundary_conditions is not None:
        model["nodes"][node_index]["boundary_conditions"] = node_update.boundary_conditions
    
    return model["nodes"][node_index]

@router.delete("/{project_id}/models/{model_id}/nodes/{node_id}")
def delete_node(
    project_id: int,
    model_id: int,
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Check if node exists
    node = next((n for n in model["nodes"] if n["id"] == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Check if node is used in any elements
    if any(e["start_node"] == node_id or e["end_node"] == node_id for e in model["elements"]):
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete node that is used in elements. Delete the elements first."
        )
    
    # Remove the node
    model["nodes"] = [n for n in model["nodes"] if n["id"] != node_id]
    
    return {"message": "Node deleted successfully"}