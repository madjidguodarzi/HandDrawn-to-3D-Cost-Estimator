from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List

from backend.app import schemas, database
from backend.app.services.projects.project_service import ProjectService
from backend.app.repositories import WallRepository, RoomRepository, CostItemRepository
from backend.app.models.wall import Wall
from backend.app.models.room import Room
from backend.app.models.cost_item import CostItem
from backend.app.models.room_objects import RoomObject
from backend.app.services.projects.cost_suggestion_service import CostSuggestionService

router = APIRouter(prefix="/project", tags=["Rooms"])

@router.get("/{project_id}/rooms", response_model=List[schemas.RoomRead])
def list_rooms(project_id: int, db: Session = Depends(database.get_db)):
    """Retrieve all rooms associated with a specific project."""
    project = ProjectService.get(db, project_id)
    return RoomRepository.get_by_project(db, project_id)

@router.post("/{project_id}/room", response_model=schemas.RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(project_id: int, room_in: schemas.RoomCreate, db: Session = Depends(database.get_db)):
    """Create a single room within a project."""
    project = ProjectService.get(db, project_id)
    if room_in.project_id != project_id:
        raise HTTPException(status_code=400, detail="Room project_id must match URL")
    return RoomRepository.create(db, room_in)

@router.post("/{project_id}/rooms", response_model=List[schemas.RoomRead], status_code=status.HTTP_201_CREATED)
def create_rooms_batch(
    project_id: int,
    rooms_in: List[schemas.RoomRead] = Body(...),
    db: Session = Depends(database.get_db),
):
    """
    Bulk create rooms with their coordinates and object relations.
    This endpoint handles the atomic creation of rooms, polygons, and surface objects (walls/floors/ceilings).
    """
    ProjectService.get(db, project_id)

    rooms_data = [
        r.model_dump(exclude={"id", "project_id", "created_at"}, exclude_none=True)
        for r in rooms_in
    ]

    created_rooms = RoomRepository.create_batch(db, project_id, rooms_data)

    return [schemas.RoomRead.model_validate(r) for r in created_rooms]

@router.get("/{project_id}/rooms/{room_id}", response_model=schemas.RoomRead)
def get_room(project_id: int, room_id: int, db: Session = Depends(database.get_db)):
    """Retrieve detailed information for a specific room, including related objects and costs."""
    room = RoomRepository.get_by_id(db, room_id)  # ✅ اکنون با eager load
    if not room or room.project_id != project_id:
        raise HTTPException(status_code=404, detail="Room not found in this project")
    return room

@router.put("/{project_id}/rooms/{room_id}", response_model=schemas.RoomRead)
def update_room(project_id: int, room_id: int, room_in: schemas.RoomUpdate, db: Session = Depends(database.get_db)):
    """Update attributes of an existing room."""
    room = RoomRepository.get_by_id(db, room_id)
    if not room or room.project_id != project_id:
        raise HTTPException(status_code=404, detail="Room not found in this project")
    return RoomRepository.update(db, room, room_in)

@router.delete("/{project_id}/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(project_id: int, room_id: int, db: Session = Depends(database.get_db)):
    """Delete a room and its associated coordinates and objects."""
    room = RoomRepository.get_by_id(db, room_id)
    if not room or room.project_id != project_id:
        raise HTTPException(status_code=404, detail="Room not found in this project")
    RoomRepository.delete(db, room)

@router.post("/{project_id}/rooms/{room_id}/suggest-costs", response_model=schemas.RoomCostSuggestionResponse)
def suggest_room_costs(
    project_id: int,
    room_id: int,
    request: schemas.RoomCostSuggestionRequest,
    db: Session = Depends(database.get_db),
):
    """
    Generate and save cost estimates for a room based on its type.
    Uses a hybrid approach: Template-based rules + AI prediction (if available).
    """
    created = CostSuggestionService.suggest_and_create(
        db, project_id, room_id, request.room_type
    )
    return schemas.RoomCostSuggestionResponse(
        room_id=room_id,
        room_type=request.room_type,
        created_costs=created,
        message=f"Created {len(created)} cost items for {request.room_type}",
    )