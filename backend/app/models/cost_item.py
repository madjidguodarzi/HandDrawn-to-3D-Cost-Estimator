from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Numeric, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum, func, event

from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

class UnitEnum(str, enum.Enum):
    """Standard units of measurement for construction cost items."""
    m2 = "m2"
    m = "m"
    piece = "piece"
    liter = "liter"
    kg = "kg"
    hour = "hour"

class CostItem(Base):
    """
    Represents a single cost line item (material, labor, or service) 
    associated with an architectural object via RoomObject.

    Attributes:
        relation_id: Foreign key to 'room_objects.id'. Links costs to walls, floors, or ceilings.
        total_price: Auto-calculated total (quantity * unit_price). Updated by repository logic.
        source: Origin of the record ('manual' for user input, 'ai_predicted' for ML estimates).
        predicted_price: Price estimated by the XGBoost model, if applicable.
    """
    __tablename__ = "cost_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Junction table relationship - costs belong to objects, not directly to rooms/walls
    relation_id: Mapped[int] = mapped_column(
        ForeignKey("room_objects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID of the architectural object this cost belongs to"
    )
    
    item_name: Mapped[str] = mapped_column(String(200), comment="Descriptive name of the item")
    category: Mapped[Optional[str]] = mapped_column(String(100), comment="Cost category (e.g., Tiling, Painting)")
    
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), comment="Physical quantity required")
    unit: Mapped[UnitEnum] = mapped_column(SAEnum(UnitEnum), comment="Unit of measurement")
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), comment="Price per unit in project currency")

    # Calculation & Scheduling fields
    total_price: Mapped[float] = mapped_column(Numeric(14, 2), comment="Calculated as quantity * unit_price")
    
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, default=1, comment="Execution duration in days")
    start_date: Mapped[Optional[str]] = mapped_column(String(50), comment="Planned start date (YYYY-MM-DD)")
    predecessor_id: Mapped[Optional[int]] = mapped_column(Integer, comment="Predecessor ID for Gantt chart dependencies")
    
    material_quality: Mapped[Optional[str]] = mapped_column(String(50), comment="Quality tier (Standard, Premium, Luxury)")
    labor_included: Mapped[bool] = mapped_column(Boolean, default=True, comment="Whether installation labor is included in price")
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="Additional remarks or specifications")
    source: Mapped[str] = mapped_column(String(30), default="manual", comment="Data origin: manual | ai_predicted | template")
    
    predicted_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), comment="XGBoost predicted unit price")
    prediction_confidence: Mapped[Optional[float]] = mapped_column(Float, comment="Model confidence score for prediction")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    relation: Mapped["RoomObject"] = relationship(back_populates="cost_items")

@event.listens_for(CostItem, "before_insert")
@event.listens_for(CostItem, "before_update")
def receive_before_insert(mapper, connection, target):
    """Automatically calculate total_price before saving."""
    if target.quantity is not None and target.unit_price is not None:
        target.total_price = float(target.quantity) * float(target.unit_price)