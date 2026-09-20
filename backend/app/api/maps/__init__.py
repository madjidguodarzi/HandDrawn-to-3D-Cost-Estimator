from fastapi import APIRouter
from backend.app.api.maps import walls, rooms, export

router = APIRouter(prefix="/maps")

router.include_router(walls.router)
router.include_router(rooms.router) 
router.include_router(export.router)