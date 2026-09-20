"""
Main entry point for the Smart Construction Cost Estimator & 3D Mapper API.
Initializes the FastAPI application, database, and routers.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from backend.app.database import init_db
from backend.app.api import ui_router, api_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the application.
    Initializes the database tables on startup.
    """
    init_db()
    yield

app = FastAPI(
    title="Smart Construction Cost Estimator & 3D Mapper",
    version="2.0.0",
    lifespan=lifespan
)


# CORS Configuration
# Note: In production, restrict allow_origins to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (for HTML/CSS/JS)
# Mounts the 'static' directory to serve frontend assets
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(ui_router)
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Run the application with Uvicorn server
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=False)