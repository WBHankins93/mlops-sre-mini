from fastapi import FastAPI
from pydantic import BaseModel, Field
from pathlib import Path
import pickle

app = FastAPI(title="Iris API (serving, no-metrics)", version="0.1.0")

class PredictIn(BaseModel):
    sepal_length: float = Field(..., description="Sepal length (cm)")
    sepal_width:  float = Field(..., description="Sepal width (cm)")
    petal_length: float = Field(..., description="Petal length (cm)")
    petal_width:  float = Field(..., description="Petal width (cm)")

# Locate model for local runs (repo root). We'll add container path logic later.
MODEL_PATH = Path(__file__).resolve().parents[1] / "model.pkl"
if not MODEL_PATH.exists():
    raise RuntimeError(
        f"Model not found at {MODEL_PATH}. Did you run `python train/train.py`?"
    )

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

@app.get("/healthz")
def healthz():
    """Simple readiness/liveness probe target."""
    return {"status": "ok"}

@app.post("/predict")
def predict(inp: PredictIn):
    """Return class id (0..2) for the Iris sample."""
    try:
        X = [[inp.sepal_length, inp.sepal_width, inp.petal_length, inp.petal_width]]
        pred = model.predict(X)  # scikit-learn estimator
        return {"class_id": int(pred[0])}
    except Exception as e:
        # keep minimal error surface for now; we’ll add counters in the metrics checkpoint
        raise HTTPException(status_code=400, detail=f"prediction_failed: {e}")