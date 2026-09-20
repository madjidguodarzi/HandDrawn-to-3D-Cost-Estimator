"""
Service layer for room detection and processing.
Orchestrates the conversion of wall data into structured room objects using topological algorithms.
"""
from typing import List, Dict, Optional
from backend.app.core.room_detector import RoomDetector
from backend.app.schemas.wall import WallRead
from backend.app.schemas.room import RoomRead, RoomCoordinateItem, RelatedObject


class RoomProcessingService:
    """Orchestrates room segmentation from validated wall data."""

    @staticmethod
    def detect_rooms(walls: List[WallRead]) -> List[RoomRead]:
        """
        Detects enclosed spaces using topological face traversal.

        Note:
            - Input walls must have valid DB IDs (post-Human Check).
            - Output rooms are pre-persistence (id=None, project_id=None).
            - Coordinates are kept in pixel units (float) for frontend consistency.
            - related_objects contain placeholder relation_ids (0) until saved to DB.

        Args:
            walls: List of validated WallRead objects with assigned IDs.

        Returns:
            List of RoomRead objects populated with coordinates and related_objects.
        """
        # Create lookup map for O(1) wall coordinate access
        wall_map: Dict[int, WallRead] = {
            w.id: w for w in walls if w.id is not None
        }

        # Prepare integer tuples for Core Algorithm
        walls_for_detector = [
            (w.id, int(w.x1), int(w.y1), int(w.x2), int(w.y2))
            for w in walls
            if w.id is not None
        ]

        # Execute Face Traversal Algorithm
        detector = RoomDetector()
        raw_rooms = detector.detect_rooms(walls_for_detector)

        # Enrich output with full wall metadata
        result = []
        for room in raw_rooms:
            related_objs: List[RelatedObject] = []
            
            for wid in room.get("wall_ids", []):
                wall_data = wall_map.get(wid)
                if wall_data:
                    related_objs.append(RelatedObject(
                        relation_id=0,  # Placeholder until DB persistence
                        object_type="wall",
                        wall_id=wid,
                        wall_x1=wall_data.x1,
                        wall_y1=wall_data.y1,
                        wall_x2=wall_data.x2,
                        wall_y2=wall_data.y2,
                        cost_items=[]   # Costs loaded separately via Repository
                    ))

            result.append(RoomRead(
                coordinates=[
                    RoomCoordinateItem(x=float(p[0]), y=float(p[1]))
                    for p in room["coordinates"]
                ],
                floor_area_m2=room["area"],
                related_objects=related_objs
            ))
        
        return result