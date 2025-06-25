from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.db.database import get_db
from backend.db.models import Model, Project, User
from backend.auth.auth_handler import AuthHandler
from backend.core.model import StructuralModel
from backend.bim.bim_engine import BIMEngine

router = APIRouter(prefix="/bim", tags=["bim"])


class IFCExportRequest(BaseModel):
    file_path: str = None
    version: str = "IFC4"


class GLTFExportRequest(BaseModel):
    file_path: str = None
    include_materials: bool = True
    include_analysis_results: bool = False


class DXFExportRequest(BaseModel):
    file_path: str = None
    view_type: str = "plan"
    include_dimensions: bool = True
    include_annotations: bool = True


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


@router.post("/{model_id}/export/ifc")
def export_to_ifc(
    model_id: int,
    request: IFCExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Export to IFC
    try:
        results = bim_engine.export_to_ifc(request.file_path, request.version)
        
        if results["status"] == "success":
            return {
                "message": "IFC export completed successfully",
                "file_path": results["file_path"],
                "file_size": results["file_size"],
                "elements_exported": results["elements_exported"],
                "version": results["version"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Export failed: {results.get('message', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export execution failed: {str(e)}")


@router.post("/{model_id}/export/gltf")
def export_to_gltf(
    model_id: int,
    request: GLTFExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Export to glTF
    try:
        results = bim_engine.export_to_gltf(
            request.file_path, 
            request.include_materials, 
            request.include_analysis_results
        )
        
        if results["status"] == "success":
            return {
                "message": "glTF export completed successfully",
                "file_path": results["file_path"],
                "file_size": results["file_size"],
                "elements_exported": results["elements_exported"],
                "include_materials": results["include_materials"],
                "include_analysis": results["include_analysis"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Export failed: {results.get('message', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export execution failed: {str(e)}")


@router.post("/{model_id}/export/dxf")
def export_to_dxf(
    model_id: int,
    request: DXFExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Export to DXF
    try:
        results = bim_engine.export_to_dxf(
            request.file_path,
            request.view_type,
            request.include_dimensions,
            request.include_annotations
        )
        
        if results["status"] == "success":
            return {
                "message": "DXF export completed successfully",
                "file_path": results["file_path"],
                "file_size": results["file_size"],
                "view_type": results["view_type"],
                "elements_exported": results["elements_exported"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Export failed: {results.get('message', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export execution failed: {str(e)}")


@router.get("/{model_id}/web-viewer")
def get_web_viewer_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Get model for web viewer
    try:
        results = bim_engine.get_model_for_web_viewer()
        
        if results["status"] == "success":
            return results
        else:
            raise HTTPException(status_code=400, detail=f"Model preparation failed: {results.get('message', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model preparation failed: {str(e)}")


@router.get("/{model_id}/export-history")
def get_export_history(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Get export history
    history = bim_engine.get_export_history()
    
    return {
        "model_id": model_id,
        "exports": history
    }


@router.post("/{model_id}/export/package")
def export_drawing_package(
    model_id: int,
    output_dir: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Export complete drawing package
    try:
        results = bim_engine.export_drawing_package(output_dir)
        
        if results["status"] == "success":
            return {
                "message": "Drawing package exported successfully",
                "output_directory": results["output_directory"],
                "summary": results["summary"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Package export failed: {results.get('message', 'Unknown error')}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package export failed: {str(e)}")


@router.delete("/{model_id}/export-files")
def clear_old_exports(
    model_id: int,
    older_than_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify model access
    model = verify_model_access(model_id, db, current_user)
    
    # Create structural model and BIM engine
    structural_model = StructuralModel(db, model_id=model_id)
    bim_engine = BIMEngine(structural_model)
    
    # Clear old export files
    result = bim_engine.clear_export_files(older_than_days)
    
    return {
        "message": f"Cleared {result['deleted_files']} old export files",
        "deleted_files": result["deleted_files"]
    }
