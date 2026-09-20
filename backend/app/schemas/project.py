from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class ProjectBase(BaseModel):
    """Base schema for project data validation."""
    name: str = Field(..., min_length=1, max_length=200, description="Name of the construction project")
    description: Optional[str] = Field(None, description="Detailed description of the project scope")
    location: Optional[str] = Field(None, description="Physical location or address of the project")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 currency code (e.g., USD, EUR)")
    map_image_base64: Optional[str] = Field(None, description="Base64 encoded string of the floor plan image")

class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass

class ProjectUpdate(BaseModel):
    """Schema for updating existing project fields. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated project name")
    description: Optional[str] = Field(None, description="Updated project description")
    location: Optional[str] = Field(None, description="Updated project location")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Updated currency code")
    map_image_base64: Optional[str] = Field(None, description="Updated base64 image string")

class ProjectRead(ProjectBase):
    """Schema for reading project data from the database."""
    id: int
    public_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)