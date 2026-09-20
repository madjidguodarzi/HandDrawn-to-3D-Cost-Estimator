from fastapi import APIRouter, Body
from typing import List
from backend.app.schemas.wall import WallRead
from backend.app.schemas.room import RoomRead
from backend.app.services.maps.export import ExportProcessingService

router = APIRouter(prefix="/export/sh3d", tags=["Process Map"])


@router.post("")
async def export_sh3d(
    walls: List[WallRead] = Body(...),
    rooms: List[RoomRead] = Body(...),
):
    """
    Generates a Sweet Home 3D (.sh3d) file from validated walls and rooms.
    
    Args:
        walls: List of validated wall segments.
        rooms: List of detected room polygons.
        
    Returns:
        A ZIP file response containing the .sh3d project.
    """
    return ExportProcessingService.generate_sh3d(walls, rooms)