# backend/app/api/projects/object_costs.py
"""
API endpoints for managing cost items associated with specific architectural objects 
(walls, floors, ceilings) via the RoomObject junction table.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app import schemas, database
from backend.app.repositories.cost_item_repo import CostItemRepository
from backend.app.models.room_objects import RoomObject

router = APIRouter(prefix="/project", tags=["Object Costs"])


def _get_relation(db: Session, project_id: int, object_id: int) -> RoomObject:
    """
    Validates that the RoomObject exists and belongs to the specified project.
    
    Args:
        db: Database session.
        project_id: The ID of the project for security scoping.
        object_id: The ID of the RoomObject.
        
    Returns:
        The RoomObject instance.
        
    Raises:
        HTTPException: 404 if the object is not found or doesn't belong to the project.
    """
    rel = db.get(RoomObject, object_id)
    if not rel or rel.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found in this project")
    return rel

@router.get("/{project_id}/objects/{object_id}/cost", response_model=List[schemas.CostItemRead])
def list_object_costs(project_id: int, object_id: int, db: Session = Depends(database.get_db)):
    """
    Lists all cost items associated with a specific architectural object.
    """
    rel = _get_relation(db, project_id, object_id)
    return rel.cost_items

@router.post("/{project_id}/objects/{object_id}/cost", response_model=schemas.CostItemRead, status_code=status.HTTP_201_CREATED)
def create_object_cost(project_id: int, object_id: int, cost_in: schemas.CostItemCreate, db: Session = Depends(database.get_db)):
    """
    Creates a new cost item for a specific architectural object.
    Automatically links the cost to the object via relation_id.
    """
    rel = _get_relation(db, project_id, object_id)
    # Ensure the cost is linked to the correct object
    cost_in.relation_id = object_id
    return CostItemRepository.create(db, cost_in)


@router.get("/{project_id}/objects/{object_id}/cost/{cost_id}", response_model=schemas.CostItemRead)
def get_object_cost(project_id: int, object_id: int, cost_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieves a specific cost item by its ID, ensuring it belongs to the specified object.
    """
    rel = _get_relation(db, project_id, object_id)
    cost = CostItemRepository.get_by_id(db, cost_id)
    if not cost or cost.relation_id != object_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost item not found for this object"
        )
    return cost


@router.put("/{project_id}/objects/{object_id}/cost/{cost_id}", response_model=schemas.CostItemRead)
def update_object_cost(project_id: int, object_id: int, cost_id: int, cost_in: schemas.CostItemUpdate, db: Session = Depends(database.get_db)):
    """
    Updates an existing cost item for a specific architectural object.
    """
    rel = _get_relation(db, project_id, object_id)
    cost = CostItemRepository.get_by_id(db, cost_id)
    if not cost or cost.relation_id != object_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost item not found for this object"
        )
    return CostItemRepository.update(db, cost, cost_in)


@router.delete("/{project_id}/objects/{object_id}/cost/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_object_cost(project_id: int, object_id: int, cost_id: int, db: Session = Depends(database.get_db)):
    """
    Deletes a specific cost item from an architectural object.
    """
    rel = _get_relation(db, project_id, object_id)
    cost = CostItemRepository.get_by_id(db, cost_id)
    if not cost or cost.relation_id != object_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost item not found for this object"
        )
    CostItemRepository.delete(db, cost)