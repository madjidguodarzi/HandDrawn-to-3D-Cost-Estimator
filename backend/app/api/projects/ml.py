from pydantic import BaseModel, Field
from fastapi import APIRouter , status
from backend.app.services.projects.data_generator import generate_synthetic_data
from backend.app.services.projects.ml_estimator import CostEstimator
from backend.app.schemas.ml_schema import CostEstimationRequest, CostEstimationResponse


estimator = CostEstimator()
router = APIRouter(prefix="/project", tags=["Costs"])

@router.post("/ml/generate/{num_samples}")
def ml_generate(num_samples: int = 3000):
    """Generates synthetic training data for ML models."""
    generate_synthetic_data(num_samples)

@router.post("/ml/train")
def ml_train():
    """Trains XGBoost models for all unique items in the dataset."""
    result = estimator.train_from_csv()
    result = estimator.train_from_csv()
    if result.get("status") == "error":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message"))
    return result

@router.get("/ml/evaluate")
def evaluate_model():
    """Evaluates the performance of trained models (RMSE)."""
    return estimator.evaluate_model()

class ItemEstimateRequest(BaseModel):
    item_name: str = Field(..., description="Item Name")
    area_m2: float = Field(..., gt=0, description="Area")
    room_type: str = Field(..., description="Rom Type")
    quality: str = Field(..., description="Quality")

@router.post("/ml/estimate-item")
def estimate_item_cost(request: ItemEstimateRequest):
    """
    Estimates the cost of a specific item using the Multi-Model Architecture.
    Loads the specific model for the 'item_name' dynamically.
    """
    
    result = estimator.estimate_item_cost(
        item_name=request.item_name,
        area_m2=request.area_m2,
        room_type=request.room_type,
        quality=request.quality
    )
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        
    return result