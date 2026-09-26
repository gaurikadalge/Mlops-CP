from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import mlflow
import os

# Initialize FastAPI
app = FastAPI(
    title="Adaptive IDS Inference API",
    description="Real-time inference endpoint for the Adaptive Historical Memory IDS model."
)

# Placeholder for our loaded model
model = None

# We can define a simplified Pydantic model representing network traffic features
class NetworkTrafficFeature(BaseModel):
    # A generic dictionary since CIC-IDS2017 has 70+ features
    features: dict

@app.on_event("startup")
def load_model():
    """
    On API startup, attempt to load the latest XGBoost model from MLflow.
    If no model is found, the API will still start but predict will fail until a model is trained.
    """
    global model
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
    mlflow.set_tracking_uri(tracking_uri)
    
    try:
        # In a real environment, you would load by Model Registry Stage (e.g., "Production")
        # Here we do a simple query to get the last successful run's model
        experiment = mlflow.get_experiment_by_name("Adaptive_IDS_Experiment")
        if experiment:
            runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id], order_by=["start_time DESC"], max_results=1)
            if not runs.empty:
                run_id = runs.iloc[0].run_id
                model_uri = f"runs:/{run_id}/model"
                model = mlflow.xgboost.load_model(model_uri)
                print(f"Model loaded successfully from run {run_id}")
    except Exception as e:
        print(f"Failed to load model from MLflow: {e}")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
def predict(traffic: NetworkTrafficFeature):
    """
    Accepts a JSON payload of network traffic features and returns a prediction.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded. Please run an experiment first.")
    
    try:
        # Convert dictionary to single-row DataFrame
        df = pd.DataFrame([traffic.features])
        
        # Make prediction (0 = Benign, 1 = Attack)
        prediction = model.predict(df)[0]
        
        return {
            "prediction": int(prediction),
            "label": "Attack" if prediction == 1 else "Benign"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
