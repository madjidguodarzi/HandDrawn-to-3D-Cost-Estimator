from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

class Project(Base):
    """
    Represents a construction project containing walls, rooms, and cost estimates.
    Uses UUID for public-facing IDs to enhance security and prevent enumeration.
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Stores the original floor plan image as a base64 string
    map_image_base64: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Use string references for relationships to avoid circular import issues during initialization
    walls: Mapped[List["Wall"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    rooms: Mapped[List["Room"]] = relationship(back_populates="project", cascade="all, delete-orphan")