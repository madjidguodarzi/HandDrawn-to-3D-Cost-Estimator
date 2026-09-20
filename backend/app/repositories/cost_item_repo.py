from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.models.cost_item import CostItem
from backend.app.schemas.cost_item import CostItemCreate, CostItemUpdate
from sqlalchemy import select


class CostItemRepository:
    """
    Data access layer for CostItem entities.
    Handles CRUD operations and automatic financial calculations.
    """

    @staticmethod
    def create(db: Session, obj_in: CostItemCreate) -> CostItem:
        """
        Creates a cost item with auto-calculated total price.
        Formula: total_price = quantity * unit_price
        """
        data = obj_in.model_dump()
        total_price = float(data["quantity"]) * float(data["unit_price"])
        db_obj = CostItem(**data, total_price=total_price)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[CostItem]:
        """Retrieves cost item by primary key."""
        return db.get(CostItem, id)

    @staticmethod
    def update(db: Session, db_obj: CostItem, obj_in: CostItemUpdate) -> CostItem:
        """
        Updates cost item and recalculates total_price if financial fields change.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Recalculate total when quantity or unit_price changes
        if "quantity" in update_data or "unit_price" in update_data:
            qty = update_data.get("quantity", db_obj.quantity)
            price = update_data.get("unit_price", db_obj.unit_price)
            db_obj.total_price = float(qty) * float(price)

        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: CostItem) -> None:
        """Deletes a cost item record."""
        db.delete(db_obj)
        db.commit()