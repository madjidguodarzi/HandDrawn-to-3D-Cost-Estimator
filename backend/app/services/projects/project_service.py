from sqlalchemy.orm import Session
from typing import List
from backend.app.repositories import ProjectRepository
from backend.app.schemas.project import ProjectCreate, ProjectUpdate
from fastapi import HTTPException, status


class ProjectService:
    """
    Service layer for managing Project entities.
    Handles business logic and delegates data access to ProjectRepository.
    """

    @staticmethod
    def create(db: Session, obj_in: ProjectCreate):
        """
        Creates a new project in the database.
        
        Args:
            db: Database session.
            obj_in: Project creation schema.
            
        Returns:
            The created Project object.
        """
        return ProjectRepository.create(db, obj_in)

    @staticmethod
    def get(db: Session, project_id: int):
        """
        Retrieves a project by its ID. Raises 404 if not found.
        
        Args:
            db: Database session.
            project_id: The ID of the project.
            
        Returns:
            The Project object.
            
        Raises:
            HTTPException: If project is not found.
        """
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100) -> List:
        """
        Lists projects with pagination.
        
        Args:
            db: Database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of Project objects.
        """
        return ProjectRepository.get_all(db, skip, limit)

    @staticmethod
    def update(db: Session, project_id: int, obj_in: ProjectUpdate):
        """
        Updates an existing project.
        
        Args:
            db: Database session.
            project_id: The ID of the project to update.
            obj_in: Project update schema.
            
        Returns:
            The updated Project object.
            
        Raises:
            HTTPException: If project is not found.
        """
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return ProjectRepository.update(db, project, obj_in)

    @staticmethod
    def delete(db: Session, project_id: int):
        """
        Deletes a project and its associated resources.
        
        Args:
            db: Database session.
            project_id: The ID of the project to delete.
            
        Raises:
            HTTPException: If project is not found.
        """
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        ProjectRepository.delete(db, project)
        return {"message": "Project deleted successfully"}