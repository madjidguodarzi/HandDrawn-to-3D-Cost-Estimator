from fastapi import APIRouter, Body
from typing import List
from backend.app.schemas.wall import WallRead
from backend.app.schemas.room import RoomRead
from backend.app.services.maps.rooms import RoomProcessingService

router = APIRouter(prefix="/process/rooms", tags=["Process Map"])


@router.post("", response_model=List[RoomRead])
async def detect_rooms(walls: List[WallRead] = Body(...)):
    """
    Detects rooms from validated walls.

    Args:
        walls: List of WallRead objects with valid database IDs.
        
    Returns:
        List of detected RoomRead objects (pre-persistence).
    """
    # Pass-through logic; the service handles the conversion to List[RoomRead]
    return RoomProcessingService.detect_rooms(walls)