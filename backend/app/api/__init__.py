"""
API Router Aggregation Module.

This module consolidates all sub-routers into two main entry points:
- ui_router: Handles direct HTML/Template responses for the frontend.
- api_router: Handles all JSON-based RESTful endpoints, grouped by domain.
"""

from fastapi import APIRouter

# Import UI routes (HTML/Templates)
from backend.app.api import ui

# Import API domain modules
from backend.app.api.projects import base, ml, plan, rooms, walls, object_costs, reports
from backend.app.api import maps

# --- UI Router ---
# Handles direct page rendering (e.g., index.html, project views)
ui_router = APIRouter(tags=["GUI"])
ui_router.include_router(ui.router)

# --- Main API Router ---
# Handles all data operations, ML, and processing endpoints
api_router = APIRouter()

# Project Management & Data
api_router.include_router(base.router)
api_router.include_router(plan.router)
api_router.include_router(walls.router)
api_router.include_router(rooms.router)
api_router.include_router(object_costs.router)

# AI & Analytics
api_router.include_router(ml.router)
api_router.include_router(reports.router)

# Image Processing Pipeline
api_router.include_router(maps.router)