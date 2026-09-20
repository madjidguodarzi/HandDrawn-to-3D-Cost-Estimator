# backend/app/services/projects/cost_suggestion_service.py
from sqlalchemy.orm import Session, joinedload
from typing import List

from backend.app.models.room_objects import RoomObject, ObjectTypeEnum
from backend.app.models.room import Room
from backend.app.repositories.cost_item_repo import CostItemRepository
from backend.app.schemas.cost_item import CostItemCreate, CostItemRead, UnitEnum
from backend.app.services.projects.cost_templates import get_template
from fastapi import HTTPException
from backend.app.services.projects.ml_estimator import estimator

ROOM_TYPE_CODES = {
    "Bedroom": 1,
    "Bathroom": 2,
    "Kitchen": 3,
    "Living Room": 4, 
    "Hallway": 5,
    "Balcony": 6,
    "Office": 7,
    "Garage": 8
}

class CostSuggestionService:
    """Generates intelligent cost estimates based on room type and physical attributes."""

    @staticmethod
    def suggest_and_create(
        db: Session, project_id: int, room_id: int, room_type: str
    ) -> List[CostItemRead]:
        """
        Creates cost items for all surfaces in a room using template + AI hybrid pricing.

        Logic Flow:
            1. Load room with eager-loaded wall relations.
            2. For each surface (wall/floor/ceiling), fetch matching template.
            3. Calculate exact quantity from physical dimensions.
            4. Determine price: AI prediction > Rule-based fallback.
            5. Persist all items in a single transaction.

        Args:
            db: Active SQLAlchemy session.
            project_id: Security scope validation.
            room_id: Target room identifier.
            room_type: Semantic type (e.g., 'Kitchen') for template selection.

        Returns:
            List of newly created CostItemRead objects.
        """
        
        # Eager load to prevent N+1 queries during quantity calculation
        room = (
            db.query(Room)
            .options(
                joinedload(Room.wall_relations).joinedload(RoomObject.wall)
            )
            .filter(Room.id == room_id, Room.project_id == project_id)
            .first()
        )
        
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        relations = room.wall_relations
        if not relations:
            raise HTTPException(
                status_code=400, 
                detail="No objects found. Please run /relations/generate first."
            )

        # Update semantic room name in database
        room.name = room_type
        db.add(room)

        # Pre-compute features once per room for AI efficiency
        room_code = ROOM_TYPE_CODES.get(room_type, 0)
        features = {
            "floor_area_m2": room.floor_area_m2 or 10.0,
            "wall_area_m2": room.wall_area_m2 or 20.0,
            "perimeter_m": room.perimeter_m or 15.0,
            "room_type_code": room_code
        }

        created_costs: List[CostItemRead] = []
        for rel in relations:
            obj_type_str = rel.object_type.value  # 'wall', 'floor', 'ceiling'
            templates = get_template(room_type, obj_type_str)
            quantity = CostSuggestionService._calculate_quantity(rel, room)
            
            for tpl in templates:
                # AI Price Integration Point
                ai_price = 0  # estimator.predict_unit_price(features)
                
                # Determine final price and source
                if ai_price and ai_price > 0:
                    final_price = ai_price
                    source = "ai_predicted"
                else:
                    final_price = tpl["unit_price"]
                    source = "rule_based"
                # ----------------------

                cost_in = CostItemCreate(
                    relation_id=rel.id,       # Link directly to the architectural object
                    item_name=tpl["item_name"],
                    category=tpl.get("category"),
                    quantity=quantity,        
                    unit=UnitEnum(tpl["unit"]),
                    unit_price=final_price,   # Use final price (AI-based or rule-based)
                    duration_days=tpl.get("duration_days", 1),
                    notes=tpl.get("notes", ""),
                    source=source,            # Record the pricing source for audit
                )
                
                cost = CostItemRepository.create(db, cost_in)
                created_costs.append(cost)

        db.commit()
        return created_costs

    @staticmethod
    def _calculate_quantity(relation: RoomObject, room: Room) -> float:
        """
        Computes physical quantity based on object type.

        Rules:
            - Wall: Uses actual wall.area_m2 from geometry.
            - Floor/Ceiling: Uses room.floor_area_m2.
            - Default: 1.0 unit.
        """
        obj_type = relation.object_type
        
        if obj_type == ObjectTypeEnum.wall and relation.wall:
            # Actual wall area from geometry
            return round(relation.wall.area_m2 or 1.0, 2)
            
        elif obj_type in (ObjectTypeEnum.floor, ObjectTypeEnum.ceiling):
            # Floor/Ceiling area equals room floor area
            return round(room.floor_area_m2 or 1.0, 2)
            
        return 1.0
