from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.db.database import get_db
from backend.db.models import Model, Project, User
from backend.auth.auth_handler import AuthHandler
from backend.core.model import StructuralModel
from backend.detailing.detailing_engine import DetailingEngine

router = APIRouter(prefix="/detailing", tags=["detailing"])


class DetailingRequest(BaseModel):
    design_code: str = "IS456"
    element_ids: List[int] = None


def get_current_user(db: Session = Depends(get_db)) -> User:
    auth_handler = AuthHandler(db)
    return auth_handler.get_current_active_user()


def verify_model_access(model_id: int, db: Session, current_user: User) -> Model:
    model = db.query(Model).join(Project).filter(
        Model.id == model_id,
        Project.organization_id == current_user.organization_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model


@router.post("/{model_id}/reinforcement")
def generate_reinforcement_details(
    model_id: int,
    request: DetailingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and detailing engine
    structural_model = StructuralModel(db, model_id=model_id)
    detailing_engine = DetailingEngine(structural_model)
    
    # Generate reinforcement details
    try:
        results = detailing_engine.generate_reinforcement_details(
            request.design_code, request.element_ids
        )
        
        if results["status"] == "completed":
            return {
                "message": "Reinforcement detailing completed successfully",
                "design_code": results["design_code"],
                "elements_detailed": results["elements_detailed"],
                "summary": results["summary"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Detailing failed: {results.get('error', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detailing execution failed: {str(e)}")


@router.get("/{model_id}/bar-schedule")
def get_bar_bending_schedule(
    model_id: int,
    element_ids: List[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and detailing engine
    structural_model = StructuralModel(db, model_id=model_id)
    detailing_engine = DetailingEngine(structural_model)
    
    # Generate bar bending schedule
    try:
        results = detailing_engine.generate_bar_bending_schedule(element_ids)
        
        if results["status"] == "completed":
            return results
        else:
            raise HTTPException(status_code=400, detail=f"Schedule generation failed: {results.get('error', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schedule generation failed: {str(e)}")


@router.get("/{model_id}/quantities")
def get_quantity_takeoff(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and detailing engine
    structural_model = StructuralModel(db, model_id=model_id)
    detailing_engine = DetailingEngine(structural_model)
    
    # Generate quantity takeoff
    try:
        results = detailing_engine.generate_quantity_takeoff()
        
        if results["status"] == "completed":
            return results
        else:
            raise HTTPException(status_code=400, detail=f"Quantity takeoff failed: {results.get('error', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quantity takeoff failed: {str(e)}")


@router.get("/{model_id}/elements/{element_id}/reinforcement")
def get_element_reinforcement_details(
    model_id: int,
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and detailing engine
    structural_model = StructuralModel(db, model_id=model_id)
    detailing_engine = DetailingEngine(structural_model)
    
    # Get element reinforcement details
    result = detailing_engine.get_element_reinforcement_details(element_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Reinforcement details not found for this element")
    
    return result


@router.delete("/{model_id}/results")
def clear_detailing_results(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and detailing engine
    structural_model = StructuralModel(db, model_id=model_id)
    detailing_engine = DetailingEngine(structural_model)
    
    # Clear all detailing results
    detailing_engine.clear_detailing_results()
    
    return {"message": "All detailing results cleared successfully"}
