from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import joblib
import pandas as pd
import os
import json
from datetime import datetime
from pathlib import Path

# ============================================================
# APP INITIALIZATION
# ============================================================
app = FastAPI(
    title="AI Agent Performance API",
    description="Multi-domain ML model serving platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODEL REGISTRY
# ============================================================
MODELS_DIR = Path("app/models")
REGISTRY_FILE = MODELS_DIR / "registry.json"

class ModelRegistry:
    """Manages multiple models across different domains"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict] = {}
        self.load_registry()
    
    def load_registry(self):
        """Load all models listed in registry.json"""
        if REGISTRY_FILE.exists():
            with open(REGISTRY_FILE, 'r') as f:
                self.metadata = json.load(f)
            
            for model_name, info in self.metadata.items():
                model_path = MODELS_DIR / info['filename']
                if model_path.exists():
                    self.models[model_name] = joblib.load(model_path)
                    print(f"✅ Loaded: {model_name}")
        else:
            self.metadata = {}
            self._save_registry()
    
    def _save_registry(self):
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def register_model(self, name: str, filename: str, domain: str, 
                       model_type: str, description: str = ""):
        """Register a new model"""
        model_path = MODELS_DIR / filename
        if not model_path.exists():
            raise FileNotFoundError(f"Model file {filename} not found")
        
        self.models[name] = joblib.load(model_path)
        self.metadata[name] = {
            "filename": filename,
            "domain": domain,
            "type": model_type,
            "description": description,
            "uploaded_at": datetime.now().isoformat()
        }
        self._save_registry()
    
    def get_model(self, name: str):
        if name not in self.models:
            raise KeyError(f"Model '{name}' not found")
        return self.models[name]
    
    def list_models(self) -> List[Dict]:
        return [
            {"name": name, **info} 
            for name, info in self.metadata.items()
        ]

registry = ModelRegistry()

# ============================================================
# REQUEST SCHEMAS
# ============================================================
class PredictionRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to use")
    features: Dict[str, Any] = Field(..., description="Feature dictionary")

class ModelUploadInfo(BaseModel):
    name: str
    domain: str
    model_type: str = "classification"
    description: str = ""

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "service": "AI Agent Performance API",
        "version": "2.0.0",
        "available_models": len(registry.models),
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "models_loaded": len(registry.models)}

@app.get("/models")
def list_models():
    """List all available models (names only)"""
    return {"models": list(registry.models.keys())}

@app.get("/models/info")
def models_info():
    """Detailed info about all models"""
    return {"models": registry.list_models()}

@app.get("/models/{model_name}")
def get_model_info(model_name: str):
    """Get info for a specific model"""
    if model_name not in registry.metadata:
        raise HTTPException(404, f"Model '{model_name}' not found")
    return registry.metadata[model_name]

@app.post("/predict")
def predict(request: PredictionRequest):
    """Make a prediction using the specified model"""
    try:
        model = registry.get_model(request.model_name)
        
        # Convert input to DataFrame (pipeline handles preprocessing)
        input_df = pd.DataFrame([request.features])
        
        # Predict
        prediction = model.predict(input_df)[0]
        
        # Get probabilities if available
        result = {
            "model_used": request.model_name,
            "prediction": str(prediction),
            "domain": registry.metadata[request.model_name]['domain']
        }
        
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(input_df)[0]
            classes = model.classes_
            result["probabilities"] = {
                str(cls): float(p) for cls, p in zip(classes, probs)
            }
            result["confidence"] = float(max(probs))
        
        return result
    
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, f"Prediction error: {str(e)}")

@app.post("/predict_batch")
async def predict_batch(model_name: str, file: UploadFile = File(...)):
    """Batch predictions from CSV"""
    try:
        model = registry.get_model(model_name)
        df = pd.read_csv(file.file)
        predictions = model.predict(df)
        
        results = df.copy()
        results['prediction'] = predictions
        
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(df)
            results['confidence'] = probs.max(axis=1)
        
        return {
            "predictions": results.to_dict(orient='records'),
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(400, f"Batch prediction error: {str(e)}")

@app.post("/models/upload")
async def upload_model(
    name: str,
    domain: str,
    model_type: str = "classification",
    description: str = "",
    file: UploadFile = File(...)
):
    """Upload a new model to the platform"""
    try:
        # Validate file extension
        if not file.filename.endswith(('.pkl', '.joblib')):
            raise HTTPException(400, "Only .pkl or .joblib files allowed")
        
        # Save file
        filename = f"{name}_{file.filename}"
        file_path = MODELS_DIR / filename
        
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Register
        registry.register_model(name, filename, domain, model_type, description)
        
        return {
            "message": f"Model '{name}' uploaded successfully",
            "filename": filename,
            "domain": domain
        }
    except Exception as e:
        raise HTTPException(400, f"Upload error: {str(e)}")

@app.delete("/models/{model_name}")
def delete_model(model_name: str):
    """Remove a model from the registry"""
    if model_name not in registry.metadata:
        raise HTTPException(404, f"Model '{model_name}' not found")
    
    filename = registry.metadata[model_name]['filename']
    file_path = MODELS_DIR / filename
    
    if file_path.exists():
        file_path.unlink()
    
    del registry.models[model_name]
    del registry.metadata[model_name]
    registry._save_registry()
    
    return {"message": f"Model '{model_name}' deleted"}

# STARTUP
@app.on_event("startup")
def startup_event():
    print(f"🚀 API started with {len(registry.models)} models loaded")