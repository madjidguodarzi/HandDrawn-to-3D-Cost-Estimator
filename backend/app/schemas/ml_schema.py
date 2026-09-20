from pydantic import BaseModel, Field

class CostEstimationRequest(BaseModel):
    """
    Request schema for ML-based cost estimation.
    """
    area: float = Field(..., gt=0, description="Area in square meters")
    room_type: str = Field(..., description="Type of room (e.g., Bedroom, Kitchen)")
    material_quality: str = Field(..., description="Material quality tier (e.g., Standard, Premium, Luxury)")

class CostEstimationResponse(BaseModel):
    """
    Response schema containing estimated costs and model confidence.
    """
    unit_price: float = Field(..., description="Estimated price per unit")
    total_cost: float = Field(..., description="Total estimated cost for the given area")
    area: float = Field(..., description="Area used for calculation")
    quality: str = Field(..., description="Quality tier used for estimation")
    confidence: str = Field(default="high", description="Model confidence level (e.g., high, medium, low)")