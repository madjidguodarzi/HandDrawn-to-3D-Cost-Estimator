from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate, ProjectUpdate, ScaleResponse
from sqlalchemy import select

class ProjectRepository:
    """Data access layer for Project entities."""
    @staticmethod
    def create(db: Session, obj_in: ProjectCreate) -> Project:
        """
        Creates a new project record in the database.
        
        Args:
            db: Active SQLAlchemy session.
            obj_in: Pydantic schema containing project data.
            
        Returns:
            Newly created Project instance with DB-generated ID.
        """
        db_obj = Project(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[Project]:
        """
        Retrieves a project by its primary key.
        
        Args:
            db: Active SQLAlchemy session.
            id: Primary key of the project.
            
        Returns:
            Project instance or None if not found.
        """
        return db.get(Project, id)

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        Retrieves a paginated list of all projects.
        
        Args:
            db: Active SQLAlchemy session.
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.
            
        Returns:
            List of Project instances.
        """
        stmt = select(Project).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update(db: Session, db_obj: Project, obj_in: ProjectUpdate) -> Project:
        """
        Updates an existing project with new data.
        
        Args:
            db: Active SQLAlchemy session.
            db_obj: Existing Project instance to update.
            obj_in: Pydantic schema containing updated fields.
            
        Returns:
            Updated Project instance.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Project) -> None:
        """
        Deletes a project record from the database.
        
        Args:
            db: Active SQLAlchemy session.
            db_obj: Project instance to delete.
        """
        db.delete(db_obj)
        db.commit()

    @staticmethod
    def get_scale(db: Session, project_id: int) -> ScaleResponse:
        """
        Retrieves the current scale ratio for a specific project.
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ScaleResponse(
            project_id=project.id,
            pixels_per_meter=project.pixels_per_meter,
            message="Scale retrieved successfully"
        )

    @staticmethod
    def update_scale(db: Session, project: Project, pixels_per_meter: float) -> Project:
        """Update the scale ratio and commit changes."""
        project.pixels_per_meter = pixels_per_meter
        db.commit()
        db.refresh(project)
        return project