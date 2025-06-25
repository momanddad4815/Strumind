from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Mock database
fake_projects_db = {}
project_counter = 0

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Project(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

def create_project_in_db(project_data: ProjectCreate, user_id: int):
    global project_counter
    project_counter += 1
    
    project = {
        "id": project_counter,
        "name": project_data.name,
        "description": project_data.description,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if user_id not in fake_projects_db:
        fake_projects_db[user_id] = {}
    
    fake_projects_db[user_id][project_counter] = project
    return project

def get_user_projects(user_id: int):
    return list(fake_projects_db.get(user_id, {}).values())

def get_project_by_id(project_id: int, user_id: int):
    user_projects = fake_projects_db.get(user_id, {})
    return user_projects.get(project_id)

def update_project_in_db(project_id: int, project_data: ProjectUpdate, user_id: int):
    project = get_project_by_id(project_id, user_id)
    if not project:
        return None
    
    if project_data.name is not None:
        project["name"] = project_data.name
    if project_data.description is not None:
        project["description"] = project_data.description
    
    project["updated_at"] = datetime.utcnow()
    return project

def delete_project_from_db(project_id: int, user_id: int):
    user_projects = fake_projects_db.get(user_id, {})
    return user_projects.pop(project_id, None) is not None

@router.post("/", response_model=Project)
def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    project_data = create_project_in_db(project, current_user["id"])
    return Project(**project_data)

@router.get("/", response_model=List[Project])
def get_projects(current_user: dict = Depends(get_current_user)):
    projects = get_user_projects(current_user["id"])
    return [Project(**project) for project in projects]

@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    project = get_project_by_id(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**project)

@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    updated_project = update_project_in_db(project_id, project, current_user["id"])
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**updated_project)

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user)
):
    if not delete_project_from_db(project_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}
