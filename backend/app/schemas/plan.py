# backend\app\schemas\plan.py

from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class PlanRead(BaseModel):
    """
    Shared schema for reading and writing map images.
    Stores the image as a base64 encoded string.
    """
    map_image_base64: str


class PlanUpdate(BaseModel):
    """
    Input schema for updating the map image.
    Used by the Service layer after converting the uploaded file to base64.
    """
    map_image_base64: str