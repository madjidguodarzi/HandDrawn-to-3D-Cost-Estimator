import os
import uuid
from typing import List
from backend.app.core.image.line_extractor import LineExtractor
from backend.app.schemas.wall import WallRead

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


class WallProcessingService:
    """Orchestrates wall detection from raw image bytes."""

    @staticmethod
    def detect_walls(image_bytes: bytes, brightness: float, contrast: float) -> List[WallRead]:
        """
        Processes an uploaded image to extract architectural walls.

        Workflow:
            1. Save image bytes to temporary storage.
            2. Run OpenCV-based line extraction with angle standardization.
            3. Convert raw coordinate tuples to WallRead schemas.
            4. Clean up temporary files.

        Args:
            image_bytes: Raw binary content of the uploaded floor plan.
            brightness: Image brightness adjustment factor (0.0 - 2.0).
            contrast: Image contrast adjustment factor (0.0 - 3.0).

        Returns:
            List of WallRead objects with id=None (pre-persistence state).
        """
        unique_id = str(uuid.uuid4())
        input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.png")

        try:
            # Write bytes to temp file for OpenCV compatibility
            with open(input_path, "wb") as f:
                f.write(image_bytes)

            # Execute core CV algorithm
            extractor = LineExtractor()
            raw_lines = extractor.process_line(
                input_path,
                brightness=brightness,
                contrast=contrast
            )

            # Transform tuples → Schema in Service layer (not API)
            return [
                WallRead(
                    x1=float(l[0]),
                    y1=float(l[1]),
                    x2=float(l[2]),
                    y2=float(l[3]),
                )
                for l in raw_lines
            ]
        finally:
            # Ensure temp file cleanup even if processing fails
            if os.path.exists(input_path):
                os.remove(input_path)