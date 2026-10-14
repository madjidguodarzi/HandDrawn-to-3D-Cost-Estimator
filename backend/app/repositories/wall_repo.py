import math
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.models.wall import Wall
from backend.app.schemas.wall import WallCreate, WallUpdate
from sqlalchemy import select


class WallRepository:
    """
    Data access layer for Wall entities.
    Handles CRUD operations and batch processing for architectural wall segments.
    """
    @staticmethod
    def create(db: Session, project_id: int, pixels_per_meter: int, wall_data: dict) -> Wall:
        """
        Creates a single wall record with auto-assigned index.

        Args:
            db: Active SQLAlchemy session.
            project_id: Parent project ID.
            wall_data: Dictionary containing wall attributes (x1, y1, x2, y2, etc.).

        Returns:
            Newly created Wall instance with generated ID.
        """
        if not isinstance(wall_data, dict):
            raise ValueError("wall_data must be a dictionary")

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        pixels_per_meter = project.pixels_per_meter

        x1=wall_data["x1"]
        y1=wall_data["y1"]
        x2=wall_data["x2"]
        y2=wall_data["y2"]
        pixel_dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        length_m = pixel_dist / pixels_per_meter if pixels_per_meter > 0 else 0
        height_m=wall_data.get("height_m", 2.70),
        area_m2=length_m * height_m,

        # Auto-assign sequential index if not provided
        if wall_data.get("index") is None:
            last_wall = db.query(Wall).filter(Wall.project_id == project_id).order_by(Wall.index.desc()).first()
            next_index = (last_wall.index + 1) if last_wall else 1
            wall_data["index"] = next_index

        # Ensure project_id is in the data
        wall_data["project_id"] = project_id
        wall_data["length_m"]=length_m
        wall_data["area_m2"]=area_m2
        
        db_obj = Wall(**wall_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # @staticmethod
    # def create_batch(db: Session, project_id: int, pixels_per_meter: int, walls_data: List[dict]) -> List[Wall]:
    #     """
    #     Bulk creates walls in a single transaction with auto-indexing.
    #     Args:
    #         db: Active SQLAlchemy session.
    #         project_id: Parent project ID.
    #         walls_data: List of dictionaries containing wall attributes.
    #     Returns:
    #         List of created Wall instances with DB-generated IDs.
    #     """
    #     if not walls_data:
    #         return []

    #     # Get the current max index to continue sequencing
    #     created_walls = []
    #     for idx, data in enumerate(walls_data):
    #         new_wall = Wall(
    #             project_id=project_id,
    #             index=idx,
    #             x1=data.get("x1"), y1=data.get("y1"),
    #             x2=data.get("x2"), y2=data.get("y2"),
    #             # side=data.get("side"),
    #             pixel_dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2),
    #             # length_m=data.get("length_m"),
    #             length_m = pixel_dist / pixels_per_meter if pixels_per_meter > 0 else 0,
    #             height_m=data.get("height_m", 2.70),
    #             area_m2=length_m * height_m,
    #             # area_m2=data.get("area_m2"),
    #             notes=data.get("notes")
    #         )
    #         db.add(new_wall)
    #         created_walls.append(new_wall)

    #     db.commit()
        
    #     # Refresh all records to get IDs and server-default values
    #     for w in created_walls:
    #         db.refresh(w)
            
    #     return created_walls

    @staticmethod
    def create_batch(db: Session, project_id: int, pixels_per_meter: float, walls_data: List[dict]) -> List[Wall]:
        """
        Bulk creates walls in a single transaction with auto-indexing and scale calculation.
        """
        if not walls_data:
            return []

        created_walls = []
        
        for idx, data in enumerate(walls_data):
            # ۱. استخراج مختصات
            x1 = data.get("x1")
            y1 = data.get("y1")
            x2 = data.get("x2")
            y2 = data.get("y2")
            height_m = data.get("height_m", 2.70)

            # ۲. محاسبه فاصله پیکسلی (اگر مختصات موجود باشند)
            pixel_dist = 0.0
            if all(v is not None for v in [x1, y1, x2, y2]):
                pixel_dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            # ۳. محاسبه طول واقعی بر اساس مقیاس
            length_m = (pixel_dist / pixels_per_meter) if pixels_per_meter > 0 else 0.0
            
            # ۴. محاسبه مساحت
            area_m2 = length_m * height_m

            # ۵. ساخت آبجکت Wall
            new_wall = Wall(
                project_id=project_id,
                index=idx, # یا می‌توانید از دیتابیس max index بگیرید
                x1=x1, y1=y1,
                x2=x2, y2=y2,
                length_m=round(length_m, 3), # گرد کردن برای تمیزی دیتابیس
                height_m=height_m,
                area_m2=round(area_m2, 3),
                notes=data.get("notes")
            )
            db.add(new_wall)
            created_walls.append(new_wall)

        db.commit()
        
        # Refresh to get DB-generated IDs
        for w in created_walls:
            db.refresh(w)
            
        return created_walls

    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[Wall]:
        """Retrieves a wall by its primary key."""
        return db.get(Wall, id)

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Wall]:
        """Returns all walls belonging to a specific project."""
        stmt = select(Wall).where(Wall.project_id == project_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update(db: Session, db_obj: Wall, obj_in: WallUpdate) -> Wall:
        """Updates wall attributes from schema."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Wall) -> None:
        """Deletes a wall record."""
        db.delete(db_obj)
        db.commit()