from __future__ import annotations
import enum
from typing import Optional, List
from sqlalchemy import Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

class ObjectTypeEnum(str, enum.Enum):
    """Defines the type of architectural object associated with a room."""
    wall = "wall"
    floor = "floor"
    ceiling = "ceiling"

class RoomObject(Base):
    """
    Junction table linking Rooms and Walls to CostItems.
    
    This table allows granular cost estimation for each physical surface 
    (e.g., painting a specific wall, tiling the floor).
    
    Attributes:
        project_id: Links to the parent project for cascading deletes.
        wall_id: Optional link to a specific wall. NULL for floor/ceiling objects.
        room_id: Link to the parent room.
        object_type: Specifies if this object is a wall, floor, or ceiling.
    """
    __tablename__ = "room_objects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Project ID for efficient cascading deletion and scope isolation
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        comment="Enables cascading deletion of all objects when project is removed"
    )
    
    wall_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("walls.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        comment="NULL for Floor/Ceiling objects"
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True,
        comment="Parent room containing this object"
    )
    
    object_type: Mapped[ObjectTypeEnum] = mapped_column(
        SAEnum(ObjectTypeEnum), 
        nullable=False,
        comment="Surface type: wall, floor, or ceiling"
    )

    # Relationships
    wall: Mapped[Optional["Wall"]] = relationship(back_populates="room_relations")
    room: Mapped["Room"] = relationship(back_populates="wall_relations")
    cost_items: Mapped[List["CostItem"]] = relationship(
        back_populates="relation",
        cascade="all, delete-orphan"
    )