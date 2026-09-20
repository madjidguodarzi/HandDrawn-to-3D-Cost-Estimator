from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

class Room(Base):
    """
    Represents a detected room or enclosed space within a construction project.
    
    Relationships:
    - coordinates: Polygon vertices defining the room's shape.
    - wall_relations: Links to RoomObject instances (walls, floors, ceilings) associated with this room.
    """
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    
    index: Mapped[int] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    
    floor_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    wall_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    perimeter_m: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="rooms")
    
    # Note: Direct cost_items are removed; costs are now linked via RoomObject (wall_relations)
    coordinates: Mapped[List["RoomCoordinate"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    wall_relations: Mapped[List["RoomObject"]] = relationship(back_populates="room", cascade="all, delete-orphan")

    @property
    def related_objects(self) -> list:
        """
        Converts wall_relations into a standardized dictionary format for the API response.
        Includes nested cost items and wall geometry for frontend rendering.
        """
        result = []
        
        # Safety check: ensure relations are loaded and not empty
        if not hasattr(self, 'wall_relations') or not self.wall_relations:
            return result
            
        for rel in self.wall_relations:
            obj = {
                "relation_id": rel.id,
                "object_type": rel.object_type.value if hasattr(rel.object_type, 'value') else str(rel.object_type),
                "wall_id": rel.wall_id,
                
                # Extract wall coordinates only if the object is a wall and the relation is loaded
                "wall_x1": rel.wall.x1 if rel.wall else None,
                "wall_y1": rel.wall.y1 if rel.wall else None,
                "wall_x2": rel.wall.x2 if rel.wall else None,
                "wall_y2": rel.wall.y2 if rel.wall else None,
                
                # Convert CostItems to simple dictionaries for the frontend
                "cost_items": [
                    {
                        "id": c.id,
                        "item_name": c.item_name,
                        "quantity": float(c.quantity),
                        "unit": c.unit.value if hasattr(c.unit, 'value') else str(c.unit),
                        "unit_price": float(c.unit_price),
                        "total_price": float(c.total_price),
                        "duration_days": c.duration_days,
                    }
                    for c in (rel.cost_items or [])  # Handle cases where cost_items might be None
                ],
            }
            result.append(obj)
            
        return result