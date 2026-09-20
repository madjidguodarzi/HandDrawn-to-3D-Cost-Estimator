# backend/app/api/projects.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app import schemas, database
from backend.app.services.projects.project_service import ProjectService

router = APIRouter(prefix="/project", tags=["Projects"])

# --- Project Base Endpoints ---

@router.post("", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project_in: schemas.ProjectCreate, db: Session = Depends(database.get_db)):
    """
    Create a new construction project.
    """
    return ProjectService.create(db, project_in)

@router.get("", response_model=List[schemas.ProjectRead])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    """
    Retrieve a list of all projects with pagination.
    """
    return ProjectService.list(db, skip, limit)

@router.get("/{project_id}", response_model=schemas.ProjectRead)
def read_project(project_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve details of a specific project by ID.
    """
    return ProjectService.get(db, project_id)

@router.put("/{project_id}", response_model=schemas.ProjectRead)
def update_project(
    project_id: int, 
    project_in: schemas.ProjectUpdate, 
    db: Session = Depends(database.get_db)
):
    """
    Update the details of an existing project.
    """
    return ProjectService.update(db, project_id, project_in)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(database.get_db)):
    """
    Delete a project and all its associated data.
    """
    ProjectService.delete(db, project_id)
