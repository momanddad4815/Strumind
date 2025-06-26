from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import Model, Project, User
from api.auth import get_current_user
from core.model import StructuralModel
from design.design_engine import DesignEngine

router = APIRouter(prefix="/design", tags=["design"])


class RCDesignRequest(BaseModel):
    design_code: str = "IS456"
    element_ids: List[int] = None


class SteelDesignRequest(BaseModel):
    design_code: str = "IS800"
    element_ids: List[int] = None


# Using the get_current_user from auth.py


def verify_model_access(model_id: int, db: Session, current_user: User) -> Model:
    model = db.query(Model).join(Project).filter(
        Model.id == model_id,
        Project.organization_id == current_user.organization_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model


@router.post("/{model_id}/rc-design")
def run_rc_design(
    model_id: int,
    request: RCDesignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and design engine
    structural_model = StructuralModel(db, model_id=model_id)
    design_engine = DesignEngine(structural_model)
    
    # Run RC design
    try:
        results = design_engine.run_rc_design(request.design_code, request.element_ids)
        
        if results["status"] == "completed":
            return {
                "message": "RC design completed successfully",
                "design_code": results["design_code"],
                "elements_designed": results["elements_designed"],
                "summary": results["summary"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Design failed: {results.get('error', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Design execution failed: {str(e)}")


@router.post("/{model_id}/steel-design")
def run_steel_design(
    model_id: int,
    request: SteelDesignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and design engine
    structural_model = StructuralModel(db, model_id=model_id)
    design_engine = DesignEngine(structural_model)
    
    # Run steel design
    try:
        results = design_engine.run_steel_design(request.design_code, request.element_ids)
        
        if results["status"] == "completed":
            return {
                "message": "Steel design completed successfully",
                "design_code": results["design_code"],
                "elements_designed": results["elements_designed"],
                "summary": results["summary"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Design failed: {results.get('error', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Design execution failed: {str(e)}")


@router.get("/{model_id}/results")
def get_design_results(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and design engine
    structural_model = StructuralModel(db, model_id=model_id)
    design_engine = DesignEngine(structural_model)
    
    # Get design summary
    summary = design_engine.get_design_summary()
    
    return summary


@router.get("/{model_id}/elements/{element_id}")
def get_element_design_result(
    model_id: int,
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and design engine
    structural_model = StructuralModel(db, model_id=model_id)
    design_engine = DesignEngine(structural_model)
    
    # Get element design results
    result = design_engine.get_element_design_results(element_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Design result not found for this element")
    
    return result


@router.delete("/{model_id}/results")
def clear_design_results(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and design engine
    structural_model = StructuralModel(db, model_id=model_id)
    design_engine = DesignEngine(structural_model)
    
    # Clear all design results
    design_engine.clear_design_results()
    
    return {"message": "All design results cleared successfully"}
