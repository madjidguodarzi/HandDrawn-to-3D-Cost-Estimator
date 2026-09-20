# backend/app/schemas/report.py
"""
Schemas for the AI-powered Natural Language to SQL reporting system.
"""
from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, Field

class ReportRequest(BaseModel):
    """
    Input from the user for generating an intelligent report.
    Contains the natural language question and optional project context.
    """
    question: str = Field(..., description="Natural language question about the project costs")
    project_id: Optional[int] = Field(None, description="Optional project ID to filter context")

class ReportResponse(BaseModel):
    """
    System output containing the original question, the generated SQL query, 
    and the resulting data from execution.
    """
    question: str
    generated_sql: str
    data: List[dict] = Field(default_factory=list, description="Raw data obtained from SQL execution")
    message: Optional[str] = Field(None, description="Success message or error details")