import base64
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

from backend.app.repositories.project_repo import ProjectRepository
from backend.app.schemas.plan import PlanRead, PlanUpdate


class PlanService:
    """
    Service layer for handling floor plan image operations.
    Manages conversion of image files to Base64 for database storage.
    """

    @staticmethod
    async def upload_plan(db: Session, project_id: int, file: UploadFile) -> PlanRead:
        """
        Converts an uploaded image file to Base64 and stores it in the project record.
        
        Args:
            db: Active SQLAlchemy session.
            project_id: ID of the project to update.
            file: The uploaded image file.
            
        Returns:
            PlanRead schema containing the Base64 string.
            
        Raises:
            HTTPException: If the file is not an image or the project is not found.
        """
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read file content
        try:
            image_bytes = await file.read()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read file: {str(e)}")

        # Convert to Base64 with data URI scheme
        base64_str = f"data:{file.content_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"

        # Verify project existence
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Update and save
        project.map_image_base64 = base64_str
        db.add(project)
        db.commit()
        db.refresh(project)

        return PlanRead(map_image_base64=project.map_image_base64)

    @staticmethod
    def get_plan(db: Session, project_id: int) -> PlanRead:
        """
        Retrieves the Base64 encoded floor plan for a specific project.
        
        Args:
            db: Active SQLAlchemy session.
            project_id: ID of the project.
            
        Returns:
            PlanRead schema containing the Base64 string.
            
        Raises:
            HTTPException: If the project or plan image is not found.
        """
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if not project.map_image_base64:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No plan image found for this project")

        return PlanRead(map_image_base64=project.map_image_base64)