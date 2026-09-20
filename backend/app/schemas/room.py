from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.cost_item import UnitEnum

class RoomCoordinateItem(BaseModel):
    x: float
    y: float
    model_config = ConfigDict(from_attributes=True)


class RelatedObject(BaseModel):
    """Represents a wall/floor/ceiling relationship connected to a room."""
    relation_id: int
    object_type: str          # "wall", "floor", "ceiling"
    wall_id: Optional[int] = None
    
    # Wall coordinates for frontend rendering
    wall_x1: Optional[float] = None
    wall_y1: Optional[float] = None
    wall_x2: Optional[float] = None
    wall_y2: Optional[float] = None

    cost_items: List["CostItemBrief"] = []
    model_config = ConfigDict(from_attributes=True)


class CostItemBrief(BaseModel):
    """نمایش خلاصه cost item در popup"""
    id: int
    item_name: str
    quantity: float
    unit: UnitEnum
    unit_price: float
    total_price: float
    duration_days: Optional[int] = 1
    
    model_config = ConfigDict(from_attributes=True)


class RoomBase(BaseModel):
    name: Optional[str] = None
    floor_area_m2: Optional[float] = None
    wall_area_m2: Optional[float] = None
    perimeter_m: Optional[float] = None
    notes: Optional[str] = None


class RoomCreate(RoomBase):
    index: Optional[int] = None
    coordinates: List[RoomCoordinateItem] = []
    wall_ids: List[int] = []


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    floor_area_m2: Optional[float] = None
    wall_area_m2: Optional[float] = None
    perimeter_m: Optional[float] = None
    notes: Optional[str] = None
    coordinates: Optional[List[RoomCoordinateItem]] = None
    wall_ids: Optional[List[int]] = None
    index: Optional[int] = None


class RoomRead(RoomBase):
    id: Optional[int] = None
    project_id: Optional[int] = None
    index: Optional[int] = None
    created_at: Optional[datetime] = None
    coordinates: List[RoomCoordinateItem] = []
    
    # ✅ جایگزین wall_ids — تمام روابط با جزئیات
    related_objects: List[RelatedObject] = []
    
    
    model_config = ConfigDict(from_attributes=True)