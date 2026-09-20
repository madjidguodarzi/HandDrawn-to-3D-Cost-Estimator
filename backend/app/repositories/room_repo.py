# backend/app/repositories/room_repo.py
"""
Data access layer for Room entities and their composite relationships.
Handles atomic creation of rooms with coordinates and object relations (walls, floors, ceilings).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional

from backend.app.models.room import Room
from backend.app.models.room_coordinate import RoomCoordinate
from backend.app.models.room_objects import RoomObject, ObjectTypeEnum

from backend.app.schemas.room import RoomCreate, RoomUpdate

class RoomRepository:
    """Data access layer for Room entities and their composite relationships."""

    @staticmethod
    def create(db: Session, obj_in: RoomCreate) -> Room:
        """Creates a basic room record."""
        db_obj = Room(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_batch(
        db: Session, project_id: int, rooms_data: List[dict]
    ) -> List[Room]:
        """
        Atomically creates rooms with coordinates and object relations.
        Each room creation includes:
        - Polygon coordinates (RoomCoordinate)
        - Wall relations (RoomObject type='wall')
        - One Floor and One Ceiling object per room (RoomObject type='floor'/'ceiling')
        
        Note: All operations occur within a single transaction.
        """
        if not rooms_data:
            return []

        created_rooms: List[Room] = []

        for idx, data in enumerate(rooms_data):
            coordinates_data = data.pop("coordinates", [])
            related_objects = data.pop("related_objects", [])

            # Create room entity
            room = Room(
                project_id=project_id,
                index=data.get("index", idx),
                name=data.get("name"),
                floor_area_m2=data.get("floor_area_m2"),
                wall_area_m2=data.get("wall_area_m2"),
                perimeter_m=data.get("perimeter_m"),
                notes=data.get("notes"),
            )
            db.add(room)
            db.flush()

            # Save polygon vertices
            for order_index, coord in enumerate(coordinates_data):
                db.add(RoomCoordinate(
                    room_id=room.id,
                    order_index=order_index,
                    x=coord["x"],
                    y=coord["y"],
                ))

            # Create floor and ceiling objects
            for wall_id in related_objects:
                db.add(RoomObject(
                    project_id=project_id,
                    wall_id=wall_id["wall_id"],
                    room_id=room.id,
                    object_type=ObjectTypeEnum.wall,
                ))

            db.add(RoomObject(
                project_id=project_id,
                wall_id=None,
                room_id=room.id,
                object_type=ObjectTypeEnum.floor,
            ))
            db.add(RoomObject(
                project_id=project_id,
                wall_id=None,
                room_id=room.id,
                object_type=ObjectTypeEnum.ceiling,
            ))
            created_rooms.append(room)
        db.commit()

        for r in created_rooms:
            db.refresh(r)
        return created_rooms

    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[Room]:
        """
        Retrieves room with eager-loaded relations to prevent N+1 queries.

        Loads: coordinates, wall_relations → wall details, cost_items
        """
        stmt = (
            select(Room)
            .where(Room.id == id)
            .options(
                selectinload(Room.coordinates),
                selectinload(Room.wall_relations)
                    .selectinload(RoomObject.wall),
                selectinload(Room.wall_relations)
                    .selectinload(RoomObject.cost_items),
            )
        )
        room = db.execute(stmt).scalar_one_or_none()
        return room

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Room]:
        """Returns all rooms for a project with full relation loading."""
        stmt = (
            select(Room)
            .where(Room.project_id == project_id)
            .options(
                selectinload(Room.coordinates),
                selectinload(Room.wall_relations)
                    .selectinload(RoomObject.wall),
                selectinload(Room.wall_relations)
                    .selectinload(RoomObject.cost_items),
            )
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def update(db: Session, db_obj: Room, obj_in: RoomUpdate) -> Room:
        """Updates room attributes from schema."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Room) -> None:
        """Deletes room and cascades to coordinates/relations."""
        db.delete(db_obj)
        db.commit()