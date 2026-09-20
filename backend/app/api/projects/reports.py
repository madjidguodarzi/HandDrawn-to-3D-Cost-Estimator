from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app import database, schemas
from backend.app.services.projects.report_service import ReportService

router = APIRouter(prefix="/project", tags=["AI Reports"])

@router.post("/report", response_model=schemas.ReportResponse)
def generate_ai_report(
    request: schemas.ReportRequest,
    db: Session = Depends(database.get_db)
):
    """
    Generates an intelligent report by converting natural language questions into SQL.
    
    This endpoint uses a local LLM to translate user queries into safe SQL statements,
    executes them against the project database, and returns the structured data.
    """
    # Validate project existence if project_id is provided
    if request.project_id:
        from backend.app.repositories.project_repo import ProjectRepository
        project = ProjectRepository.get_by_id(db, request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
    return ReportService.generate_and_execute_report(db, request)