# backend/app/schemas/room_object.py
"""
Schemas for RoomObject (Junction table linking Rooms/Walls to Costs).
These schemas handle the API contracts for managing architectural surfaces.
"""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.cost_item import UnitEnum 
from backend.app.schemas.cost_item import ObjectTypeEnum, CostItemRead

class RoomObjectBase(BaseModel):
    """Base schema for architectural objects (Walls, Floors, Ceilings)."""
    wall_id: Optional[int] = None
    object_type: ObjectTypeEnum

class RoomObjectCreate(RoomObjectBase):
    """Schema for creating a new room-object relationship manually."""
    pass

class RoomObjectUpdate(BaseModel):
    """Schema for updating room-object attributes."""
    pass

class RoomObjectRead(RoomObjectBase):
    """Schema for reading room-object details with associated costs."""
    id: int
    room_id: int
    project_id: int
    cost_items: List[CostItemRead] = []
    model_config = ConfigDict(from_attributes=True)