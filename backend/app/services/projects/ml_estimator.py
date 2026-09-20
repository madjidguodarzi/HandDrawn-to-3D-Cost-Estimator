# backend/app/services/projects/ml_estimator.py
"""
ML Cost Estimator Service.

Implements a Multi-Model Architecture where a separate XGBoost model is trained 
for each unique construction item (e.g., 'Ceramic Tile', 'Paint'). 
Models and LabelEncoders are persisted as JSON files for lightweight deployment.
"""
import xgboost as xgb
import pandas as pd
import json
from sklearn.preprocessing import LabelEncoder
import os
import re
from pathlib import Path
import numpy as np
import logging

# Configure logger
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "storage" / "ml_models" / "items"
ENCODERS_DIR = BASE_DIR / "storage" / "ml_models" / "encoders"

class CostEstimator:
    def __init__(self):
        self.models = {} 
        self.encoders = {}

    @staticmethod
    def _make_slug(text: str) -> str:
        """
        Converts an item name into a filesystem-safe slug for model storage.
        
        Args:
            text: The raw item name (e.g., 'Ceramic Tile Purchase').
            
        Returns:
            A sanitized string (e.g., 'item_ceramic_tile_purchase').
        """
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s]+', '_', text)
        return f"item_{text}"

    def _ensure_model_loaded(self, slug: str):
        if slug in self.models:
            return True
            
        model_path = MODELS_DIR / f"{slug}.json"
        encoder_path = ENCODERS_DIR / f"{slug}.json"
        
        if not model_path.exists() or not encoder_path.exists():
            logger.warning(f"Files missing for slug: {slug}")
            return False
            
        try:
            # ✅ لود مدل XGBoost از JSON (بدون تداخل ماژول)
            model_obj = xgb.XGBRegressor()
            model_obj.load_model(str(model_path))
            
            # ✅ لود انکودر از JSON
            with open(encoder_path, 'r') as f:
                encoder_data = json.load(f)
                
            le_room = LabelEncoder()
            le_qual = LabelEncoder()
            le_room.classes_ = np.array(encoder_data['room_classes'])
            le_qual.classes_ = np.array(encoder_data['quality_classes'])
            
            self.models[slug] = model_obj
            self.encoders[slug] = {'room': le_room, 'quality': le_qual}
            logger.info(f"Dynamically loaded model: {slug}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to load model {slug}: {e}")
            return False

    def train_from_csv(self, csv_path="data/item_training_data.csv"):
        if not os.path.isabs(csv_path):
            csv_path = str(BASE_DIR / csv_path)
            
        if not os.path.exists(csv_path):
            return {"status": "error", "message": f"File not found: {csv_path}"}

        df = pd.read_csv(csv_path)
        unique_items = df['item_name'].unique()
        
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        ENCODERS_DIR.mkdir(parents=True, exist_ok=True)
        
        results = {}
        trained_count = 0
        
        for item_name in unique_items:
            slug = self._make_slug(item_name)
            item_df = df[df['item_name'] == item_name].copy()
            
            if len(item_df) < 5:
                continue
                
            le_room = LabelEncoder()
            le_qual = LabelEncoder()
            item_df['room_code'] = le_room.fit_transform(item_df['room_type'])
            item_df['qual_code'] = le_qual.fit_transform(item_df['quality'])
            
            features = ['room_code', 'qual_code']
            X = item_df[features]
            y = item_df['unit_price']
            
            model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
            model.fit(X, y)
            
            # Save the model as JSON
            model.save_model(str(MODELS_DIR / f"{slug}.json"))
            
            # Save encoder as JSON
            encoder_data = {
                'room_classes': le_room.classes_.tolist(),
                'quality_classes': le_qual.classes_.tolist()
            }
            with open(ENCODERS_DIR / f"{slug}.json", 'w') as f:
                json.dump(encoder_data, f)
            
            preds = model.predict(X)
            rmse = ((y - preds) ** 2).mean() ** 0.5
            results[item_name] = round(rmse, 2)
            
            self.models[slug] = model
            self.encoders[slug] = {'room': le_room, 'quality': le_qual}
            trained_count += 1
            
        logger.info(f"Training complete. Trained {trained_count} models.")
        return {"status": "success", "items_trained": trained_count, "rmse": results}

    def estimate_item_cost(self, item_name: str, area_m2: float, room_type: str, quality: str):
        slug = self._make_slug(item_name)
        
        if not self._ensure_model_loaded(slug):
            available = [f.stem for f in MODELS_DIR.glob("*.json")] if MODELS_DIR.exists() else []
            return {
                "error": f"Model not found for '{item_name}'",
                "requested_slug": slug,
                "available_files": available,
                "models_dir": str(MODELS_DIR)
            }
            
        model = self.models[slug]
        encoders = self.encoders[slug]
        
        try:
            room_code = int(encoders['room'].transform([room_type])[0])
            qual_code = int(encoders['quality'].transform([quality])[0])
        except ValueError as e:
            return {"error": f"Invalid input: {str(e)}"}
            
        input_df = pd.DataFrame([{'room_code': room_code, 'qual_code': qual_code}])
        predicted_unit_price = float(model.predict(input_df)[0])
        total_cost = predicted_unit_price * area_m2
        
        return {
            "item_name": item_name,
            "area_m2": area_m2,
            "room_type":room_type,
            "quality": quality,
            "unit_price": round(predicted_unit_price, 2),
            "total_cost": round(total_cost, 2)
        }

estimator = CostEstimator()