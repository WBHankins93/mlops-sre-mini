from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from pathlib import Path
import pickle
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Iris API (serving, no-metrics)", version="0.1.0")

# ---- Request/Prediction Metrics ----
# Total HTTP requests by endpoint/method/status
REQUESTS = Counter(
    "requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status"],
)

# Latency histogram per endpoint (seconds)
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
)

# Prediction-specific counters
PREDICT_TOTAL = Counter(
    "predict_total",
    "Total prediction calls",
)

PREDICT_ERRORS_TOTAL = Counter(
    "predict_errors_total",
    "Total prediction errors",
)

# ---- Model load (local dev expects ./model.pkl at repo root) ----
class PredictIn(BaseModel):
    sepal_length: float = Field(..., description="Sepal length (cm)")
    sepal_width:  float = Field(..., description="Sepal width (cm)")
    petal_length: float = Field(..., description="Petal length (cm)")
    petal_width:  float = Field(..., description="Petal width (cm)")

MODEL_PATH = Path(__file__).resolve().parents[1] / "model.pkl"
if not MODEL_PATH.exists():
    raise RuntimeError(
        f"Model not found at {MODEL_PATH}. Did you run `python train/train.py`?"
    )

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# ---- Metrics middleware (records every request except /metrics) ----
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path

    # Don't self-measure the Prometheus scrape
    if endpoint == "/metrics":
        return await call_next(request)

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    REQUESTS.labels(endpoint=endpoint, method=request.method, status=str(response.status_code)).inc()

    return response

# ---- Endpoints ----
@app.get("/healthz")
def healthz():
    """Simple readiness/liveness probe target."""
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict(inp: PredictIn):
    PREDICT_TOTAL.inc()
    try:
        X = [[inp.sepal_length, inp.sepal_width, inp.petal_length, inp.petal_width]]
        pred = model.predict(X)  # scikit-learn estimator
        return {"class_id": int(pred[0])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"prediction_failed: {e}")