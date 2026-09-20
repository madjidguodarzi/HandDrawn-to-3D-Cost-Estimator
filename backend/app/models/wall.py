"""
Wall Model Definition.

Represents physical wall segments extracted from floor plan images.
Includes geometric properties (coordinates, length, area) and relationships
to rooms and cost items for industrial AI-based cost estimation.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

class Wall(Base):
    """
    Represents a physical wall segment in a construction project.
    
    Geometry Logic:
    - Coordinates (x1, y1, x2, y2) are derived from OpenCV image processing.
    - 'length_m' and 'area_m2' are auto-computed in the Pydantic schema (WallBase.compute_geometry)
      but stored here for database persistence and querying.
    """
    __tablename__ = "walls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    
    # Sequential ordering index within the project (useful for UI display order)
    index: Mapped[int] = mapped_column(Integer, comment="Sequential ordering index within project")
    
    # Geometric coordinates from image detection
    x1: Mapped[Optional[float]] = mapped_column(Float)
    y1: Mapped[Optional[float]] = mapped_column(Float)
    x2: Mapped[Optional[float]] = mapped_column(Float)
    y2: Mapped[Optional[float]] = mapped_column(Float)
    
    # Computed metrics for cost estimation
    length_m: Mapped[Optional[float]] = mapped_column(Float, comment="Calculated wall length in meters")
    height_m: Mapped[float] = mapped_column(Float, default=2.70, comment="Standard wall height in meters")
    area_m2: Mapped[Optional[float]] = mapped_column(Float,  comment="Calculated wall surface area")

    notes: Mapped[Optional[str]] = mapped_column(Text, comment="Manual notes or observations")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="walls")

    # Junction table for granular cost estimation per wall face
    room_relations: Mapped[List["RoomObject"]] = relationship(
        back_populates="wall",
        cascade="all, delete-orphan"
    )