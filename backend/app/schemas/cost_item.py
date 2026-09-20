from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.app.models.cost_item import UnitEnum
from backend.app.models.room_objects import ObjectTypeEnum

class CostItemBase(BaseModel):
    """Base schema for construction cost items."""
    item_name: str = Field(..., min_length=1, max_length=200, description="Name of the cost item")
    category: Optional[str] = Field(None, description="Category e.g., Tiling, Painting")
    quantity: float = Field(..., gt=0, description="Physical quantity required")
    unit: UnitEnum = Field(..., description="Unit of measurement")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    duration_days: Optional[int] = Field(1, description="Estimated duration in days")
    start_date: Optional[str] = Field(None, description="Planned start date YYYY-MM-DD")
    predecessor_id: Optional[int] = Field(None, description="ID of predecessor task for scheduling")
    material_quality: Optional[str] = Field(None, description="Quality tier: Standard, Premium, Luxury")
    labor_included: bool = Field(True, description="Whether labor cost is included in unit price")
    notes: Optional[str] = Field(None, description="Additional remarks")
    source: str = Field("manual", description="Data origin: manual, ai_suggestion, or template")


class CostItemCreate(CostItemBase):
    """Schema for creating a new cost item linked to a room object."""
    relation_id: int = Field(..., description="ID of the associated RoomObject (wall/floor/ceiling)")

class CostItemUpdate(BaseModel):
    """Schema for updating existing cost items."""
    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[UnitEnum] = None
    unit_price: Optional[float] = Field(None, ge=0)
    material_quality: Optional[str] = None
    labor_included: Optional[bool] = None
    notes: Optional[str] = None
    source: Optional[str] = None

class CostItemRead(CostItemBase):
    """Schema for reading cost items with database-generated fields."""
    id: int
    relation_id: int
    total_price: float
    predicted_price: Optional[float] = None
    prediction_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WallRoomRelationCreate(BaseModel):
    """Schema for creating a junction between a wall and a room."""
    wall_id: int
    room_id: int
    object_type: ObjectTypeEnum

class WallRoomRelationRead(BaseModel):
    """Schema for reading wall-room relations with associated costs."""
    id: int
    wall_id: int
    room_id: int
    object_type: ObjectTypeEnum
    costs: list[CostItemRead] = []
    model_config = ConfigDict(from_attributes=True)

class CostSuggestion(BaseModel):
    """A single cost item suggested by the AI or Rule Engine."""
    item_name: str
    category: Optional[str] = None
    quantity: float = 1.0
    unit: UnitEnum = UnitEnum.m2
    unit_price: float = 0.0
    duration_days: int = 1
    notes: Optional[str] = None


class RoomCostSuggestionRequest(BaseModel):
    """Request to generate cost suggestions based on room type."""
    room_type: str = Field(..., description="Type of room e.g., Kitchen, Bedroom")


class RoomCostSuggestionResponse(BaseModel):
    """Response containing generated cost items for a room."""
    room_id: int
    room_type: str
    created_costs: List[CostItemRead]
    message: str