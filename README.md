# mlops-sre-mini (Bare Minimum)

This is the **bare minimum** seed so we can add features step-by-step without getting lost.

## What's here now
- Tiny FastAPI app with just `/healthz`.
- Minimal dependency file for running the app.
- Empty folders kept with `.gitkeep` so future diffs stay focused.

## Quick run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --port 8000 --reload
# In another shell:
curl -s localhost:8000/healthz
```

## Planned checkpoints (we'll add one at a time)
1. **Hello service** (this commit) — ✅ `/healthz`
2. Training script (`train/train.py`) → writes `model.pkl`
3. Add `/predict` using the trained model
4. Prometheus metrics: `/metrics`, counters + histogram
5. Dockerfile (bake model), local image build
6. Helm chart (Deployment/Service/ServiceMonitor)
7. kind + kube-prometheus-stack demo
8. CI/CD: `train.yml` → `build.yml` → `deploy.yml`
9. Grafana dashboard and docs polish
