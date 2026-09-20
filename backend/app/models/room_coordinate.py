from __future__ import annotations
from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

class RoomCoordinate(Base):
    """
    Represents a single vertex (x, y) of a room's polygon.
    Used to reconstruct the geometric shape of a room from detected walls.
    """
    __tablename__ = "room_coordinates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, comment="Sequence order of points to correctly draw the polygon")
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    
    room: Mapped["Room"] = relationship(back_populates="coordinates")