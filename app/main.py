from fastapi import FastAPI

app = FastAPI(title="Iris API (bare minimum)", version="0.0.1")

@app.get("/healthz")
def healthz():
    """Simple readiness/liveness probe target."""
    return {"status": "ok"}

