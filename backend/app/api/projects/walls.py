from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List

from backend.app import schemas, database
from backend.app.services.projects.project_service import ProjectService
from backend.app.repositories import WallRepository
from backend.app.models.cost_item import CostItem
from backend.app.models.room_objects import RoomObject
router = APIRouter(prefix="/project", tags=["Walls"])

@router.get("/{project_id}/walls", response_model=List[schemas.WallRead])
def list_walls(project_id: int, db: Session = Depends(database.get_db)):
    """Retrieve all walls associated with a specific project."""
    project = ProjectService.get(db, project_id)
    return WallRepository.get_by_project(db, project_id)

@router.post("/{project_id}/wall", response_model=schemas.WallRead, status_code=status.HTTP_201_CREATED)
def create_wall(project_id: int, wall_in: schemas.WallCreate, db: Session = Depends(database.get_db)):
    """Create a single wall entry within a project."""
    wall_data = wall_in.model_dump()
    new_wall = WallRepository.create(db, project_id, wall_data)
    return schemas.WallRead.model_validate(new_wall).model_dump()

@router.post("/{project_id}/walls", response_model=List[schemas.WallRead], status_code=status.HTTP_201_CREATED)
def create_walls_batch(
    project_id: int,
    walls_in: List[schemas.WallRead] = Body(...),
    db: Session = Depends(database.get_db),
):
    """Save a batch of walls after human verification."""
    ProjectService.get(db, project_id)
    walls_data = [
        w.model_dump(exclude={"id", "project_id", "created_at"}, exclude_none=True)
        for w in walls_in
    ]
    created_walls = WallRepository.create_batch(db, project_id, walls_data)
    return [schemas.WallRead.model_validate(w) for w in created_walls]

@router.get("/{project_id}/walls/{wall_id}", response_model=schemas.WallRead)
def get_wall(project_id: int, wall_id: int, db: Session = Depends(database.get_db)):
    """Retrieve details of a specific wall."""
    wall = WallRepository.get_by_id(db, wall_id)
    if not wall or wall.project_id != project_id:
        raise HTTPException(status_code=404, detail="Wall not found in this project")
    return wall

@router.put("/{project_id}/walls/{wall_id}", response_model=schemas.WallRead)
def update_wall(project_id: int, wall_id: int, wall_in: schemas.WallUpdate, db: Session = Depends(database.get_db)):
    """Update the properties of an existing wall."""
    wall = WallRepository.get_by_id(db, wall_id)
    if not wall or wall.project_id != project_id:
        raise HTTPException(status_code=404, detail="Wall not found in this project")
    return WallRepository.update(db, wall, wall_in)

@router.delete("/{project_id}/walls/{wall_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wall(project_id: int, wall_id: int, db: Session = Depends(database.get_db)):
    """Delete a wall from the project."""
    wall = WallRepository.get_by_id(db, wall_id)
    if not wall or wall.project_id != project_id:
        raise HTTPException(status_code=404, detail="Wall not found in this project")
    WallRepository.delete(db, wall)


