from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List
from backend.app.schemas.wall import WallRead
from backend.app.services.maps.walls import WallProcessingService

router = APIRouter(prefix="/process/walls", tags=["Process Map"])


@router.post("", response_model=List[WallRead])
async def detect_walls(
    file: UploadFile = File(...),
    brightness: float = Form(1.0),
    contrast: float = Form(1.0),
):
    """
    Detects walls from an uploaded floor plan image.
    
    Args:
        file: The image file (JPG/PNG) containing the hand-drawn or scanned map.
        brightness: Brightness adjustment factor (0.0 - 2.0).
        contrast: Contrast adjustment factor (0.0 - 3.0).
        
    Returns:
        A list of detected wall segments with their coordinates.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_bytes = await file.read()
        # Process the image and extract walls
        return WallProcessingService.detect_walls(image_bytes, brightness, contrast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))