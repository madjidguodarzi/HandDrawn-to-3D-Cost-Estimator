import os
import uuid
from typing import List
from fastapi.responses import Response
from backend.app.core.sh3d_exporter import SH3DExporter
from backend.app.schemas.wall import WallRead
from backend.app.schemas.room import RoomRead


class ExportProcessingService:
    """
    Service layer for handling map exports to external formats.
    Currently supports Sweet Home 3D (.sh3d) format.
    """

    @staticmethod
    def generate_sh3d(walls: List[WallRead], rooms: List[RoomRead]) -> Response:
        """
        Generates a Sweet Home 3D file from detected walls and rooms.

        Args:
            walls: List of validated WallRead objects.
            rooms: List of detected RoomRead objects (currently unused in SH3D export but kept for consistency).

        Returns:
            FastAPI Response containing the .sh3d zip file.
        """
        file_id = str(uuid.uuid4())
        # Use a temporary path for the exporter to write intermediate XML if needed
        output_path = os.path.join("temp", f"{file_id}_output")

        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)

        # Convert WallRead schemas to simple coordinate tuples required by the core exporter
        lines = [(int(w.x1), int(w.y1), int(w.x2), int(w.y2)) for w in walls]

        exporter = SH3DExporter()
        sh3d_content = exporter.export_to_sh3d(lines=lines, output_path=output_path)

        return Response(
            content=sh3d_content,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=floor_plan_{file_id}.sh3d"},
        )