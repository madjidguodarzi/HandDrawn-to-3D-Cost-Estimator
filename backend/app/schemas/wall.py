# backend/app/schemas/wall.py
"""
Schemas for Wall entities.
Includes automatic geometry calculation (length and area) based on coordinates.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
import math

class WallBase(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    length_m: Optional[float] = None
    height_m: float = 2.70
    area_m2: Optional[float] = None
    notes: Optional[str] = None

    @model_validator(mode='after')
    def compute_geometry(self):
        """
        Automatically calculates wall length and area if not provided.
        Uses Euclidean distance for length and length * height for area.
        """
        if self.length_m is None:
            self.length_m = round(math.hypot(self.x2 - self.x1, self.y2 - self.y1), 4)

        if self.area_m2 is None and self.length_m is not None:
            self.area_m2 = round(self.length_m * self.height_m, 4)

        return self

class WallCreate(WallBase):
    """
    Schema for creating a new wall. 
    Index is optional as it is auto-assigned by the repository.
    """
    index: Optional[int] = None

class WallUpdate(BaseModel):
    """Schema for updating existing wall attributes. All fields are optional."""
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    length_m: Optional[float] = None
    height_m: Optional[float] = None
    area_m2: Optional[float] = None
    notes: Optional[str] = None
    index: Optional[int] = None

class WallRead(WallBase):
    """
    Standard output schema for walls.
    Used in API responses and internal data transfer after persistence.
    Pre-persistence objects will have id=None.
    """
    id: Optional[int] = None
    project_id: Optional[int] = None
    index: Optional[int] = None
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)