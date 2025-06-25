from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import get_current_user
from api.projects import get_project_by_id
from api.models import get_model_by_id
import uuid

router = APIRouter(prefix="/api/projects", tags=["analysis"])

# Mock database for analysis
fake_analysis_db = {}

class AnalysisRequest(BaseModel):
    analysis_type: str  # "linear", "modal", "pushover", etc.
    load_combinations: Optional[List[str]] = ["DL", "LL", "DL+LL"]
    options: Optional[Dict[str, Any]] = {}

class AnalysisStatus(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    progress: int  # 0-100
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    job_id: str
    analysis_type: str
    status: str
    results: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None

def create_analysis_job(project_id: int, model_id: int, analysis_request: AnalysisRequest, user_id: int):
    job_id = str(uuid.uuid4())
    
    # Mock analysis results
    mock_results = {
        "linear": {
            "displacements": {
                "nodes": [
                    {"node_id": 1, "dx": 0.0, "dy": 0.0, "dz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
                    {"node_id": 2, "dx": 0.002, "dy": -0.015, "dz": 0.0, "rx": 0.001, "ry": 0.0, "rz": 0.0},
                    {"node_id": 3, "dx": 0.0, "dy": 0.0, "dz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
                    {"node_id": 4, "dx": 0.001, "dy": -0.008, "dz": 0.0, "rx": 0.0005, "ry": 0.0, "rz": 0.0},
                    {"node_id": 5, "dx": 0.003, "dy": -0.025, "dz": 0.0, "rx": 0.002, "ry": 0.0, "rz": 0.0},
                    {"node_id": 6, "dx": 0.001, "dy": -0.008, "dz": 0.0, "rx": 0.0005, "ry": 0.0, "rz": 0.0}
                ]
            },
            "forces": {
                "elements": [
                    {"element_id": 1, "axial": -125.5, "shear_y": 45.2, "shear_z": 0.0, "moment_x": 0.0, "moment_y": 0.0, "moment_z": 85.3},
                    {"element_id": 2, "axial": -89.3, "shear_y": 38.1, "shear_z": 0.0, "moment_x": 0.0, "moment_y": 0.0, "moment_z": 72.1},
                    {"element_id": 3, "axial": -285.7, "shear_y": 12.5, "shear_z": 0.0, "moment_x": 0.0, "moment_y": 0.0, "moment_z": 18.9},
                    {"element_id": 4, "axial": -425.2, "shear_y": 8.3, "shear_z": 0.0, "moment_x": 0.0, "moment_y": 0.0, "moment_z": 12.7},
                    {"element_id": 5, "axial": -198.1, "shear_y": 15.1, "shear_z": 0.0, "moment_x": 0.0, "moment_y": 0.0, "moment_z": 22.8}
                ]
            },
            "reactions": {
                "nodes": [
                    {"node_id": 1, "fx": 125.5, "fy": 245.3, "fz": 0.0, "mx": 0.0, "my": 0.0, "mz": 85.3},
                    {"node_id": 3, "fx": 89.3, "fy": 198.7, "fz": 0.0, "mx": 0.0, "my": 0.0, "mz": 72.1}
                ]
            }
        },
        "modal": {
            "modes": [
                {"mode": 1, "frequency": 2.45, "period": 0.408, "mass_participation_x": 75.2, "mass_participation_y": 12.1, "mass_participation_z": 0.0},
                {"mode": 2, "frequency": 8.91, "period": 0.112, "mass_participation_x": 15.8, "mass_participation_y": 68.5, "mass_participation_z": 0.0},
                {"mode": 3, "frequency": 15.67, "period": 0.064, "mass_participation_x": 8.1, "mass_participation_y": 18.2, "mass_participation_z": 0.0}
            ],
            "total_mass": 2850.5,
            "effective_masses": {"x": 2142.3, "y": 2256.7, "z": 0.0}
        }
    }
    
    analysis_job = {
        "job_id": job_id,
        "project_id": project_id,
        "model_id": model_id,
        "user_id": user_id,
        "analysis_type": analysis_request.analysis_type,
        "status": "completed",  # Mock as completed immediately
        "progress": 100,
        "message": "Analysis completed successfully",
        "results": mock_results.get(analysis_request.analysis_type, {}),
        "created_at": datetime.utcnow(),
        "completed_at": datetime.utcnow()
    }
    
    if user_id not in fake_analysis_db:
        fake_analysis_db[user_id] = {}
    
    fake_analysis_db[user_id][job_id] = analysis_job
    return analysis_job

def get_analysis_job(job_id: str, user_id: int):
    return fake_analysis_db.get(user_id, {}).get(job_id)

def get_model_results(project_id: int, model_id: int, user_id: int):
    # Get all completed analysis jobs for this model
    user_jobs = fake_analysis_db.get(user_id, {})
    model_results = {}
    
    for job_id, job in user_jobs.items():
        if (job["project_id"] == project_id and 
            job["model_id"] == model_id and 
            job["status"] == "completed"):
            model_results[job["analysis_type"]] = job["results"]
    
    return model_results

@router.post("/{project_id}/models/{model_id}/analysis")
def run_analysis(
    project_id: int,
    model_id: int,
    analysis_request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify model exists
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Create analysis job
    job = create_analysis_job(project_id, model_id, analysis_request, current_user["id"])
    
    return {"job_id": job["job_id"], "status": "queued", "message": "Analysis job created successfully"}

@router.get("/analysis/status/{job_id}", response_model=AnalysisStatus)
def get_analysis_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    job = get_analysis_job(job_id, current_user["id"])
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    return AnalysisStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result=job["results"] if job["status"] == "completed" else None
    )

@router.get("/{project_id}/models/{model_id}/results")
def get_analysis_results(
    project_id: int,
    model_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify model exists
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    results = get_model_results(project_id, model_id, current_user["id"])
    return {
        "project_id": project_id,
        "model_id": model_id,
        "results": results,
        "available_analyses": list(results.keys())
    }

@router.get("/{project_id}/models/{model_id}/analysis/{analysis_type}")
def get_specific_analysis_results(
    project_id: int,
    model_id: int,
    analysis_type: str,
    current_user: dict = Depends(get_current_user)
):
    # Verify project exists
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify model exists
    model = get_model_by_id(project_id, model_id, current_user["id"])
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    results = get_model_results(project_id, model_id, current_user["id"])
    
    if analysis_type not in results:
        raise HTTPException(status_code=404, detail=f"No {analysis_type} analysis results found")
    
    return {
        "project_id": project_id,
        "model_id": model_id,
        "analysis_type": analysis_type,
        "results": results[analysis_type]
    }
