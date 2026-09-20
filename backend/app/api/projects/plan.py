from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from backend.app import database
from backend.app.schemas.plan import PlanRead
from backend.app.services.projects.plan_service import PlanService

router = APIRouter(prefix="/project", tags=["Plan"])


@router.get("/{project_id}/plan", response_model=PlanRead)
def get_project_plan(project_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieves the base64-encoded map image for a specific project.
    """
    return PlanService.get_plan(db, project_id)


@router.post("/{project_id}/plan", response_model=PlanRead)
async def update_project_plan(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """
    Uploads an image file and stores it as a base64 string in the project record.
    """
    return await PlanService.upload_plan(db, project_id, file)