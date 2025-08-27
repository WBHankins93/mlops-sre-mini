# Architecture & Ops — mlops-sre-mini

## Purpose

A production-lean example for **train → serve → container → Helm → Prometheus/Grafana**, with CI/CD that bakes the model into the image for a hermetic MVP.

---

## System Diagram

```
Train (scikit-learn) --> model.pkl --> Dockerfile (COPY model) 
--> Image --> Run (uvicorn) --> Helm (Deployment/Service/ServiceMonitor) 
--> Prometheus scrape --> Grafana
         |
         └── accuracy printed
```

---

## Components

### Training

- `train/train.py`: Logistic Regression on Iris
- Outputs accuracy + `model.pkl` at repo root
- Dependencies: `scikit-learn==1.5.1`, `numpy>=1.26.0`

### Serving

- `app/main.py`: FastAPI app
- **Endpoints:**
  - `/healthz` → readiness/liveness
  - `/predict` → 4 floats → `{"class_id": ...}`
  - `/metrics` → Prometheus exposition
- **Metrics:**
  - `requests_total{endpoint,method,status}`
  - `request_latency_seconds_bucket{endpoint,le}`
  - `predict_total`, `predict_errors_total`

### Container

- `Dockerfile`: Python 3.11 slim, install `app/requirements.txt`, copy `app/` + `model.pkl`
- Entrypoint: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Helm

- **Deployment**: named port `http`, probes on `/healthz`, resource requests/limits
- **Service**: exposes port 8000 → targetPort `http`
- **ServiceMonitor**: scrapes `/metrics`, `labels: { release: "monitoring" }`

### Observability

**Grafana dashboard** (`grafana/dashboards/iris-api.json`):

- **Throughput:**
  ```promql
  sum(increase(requests_total{endpoint="/predict"}[5m]))
  ```

- **Errors:**
  ```promql
  sum(increase(predict_errors_total[5m]))
  ```

- **p95 latency:**
  ```promql
  histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket{endpoint="/predict"}[5m])) by (le))
  ```

---

## SLO Examples

- p95 latency < **200ms** (rolling 5m)
- Error rate < **1%** (rolling 5m)
- Availability ≥ **99.9%** monthly

---

## Rollback Procedures

### Roll back by image SHA (preferred)

```bash
helm upgrade --install iris-api ./helm/iris-api \
  -n iris \
  --set image.repository=ghcr.io/<owner>/iris-api \
  --set image.tag=<PREVIOUS_SHA>
```

### Roll back by Helm revision

```bash
helm -n iris history iris-api
helm -n iris rollback iris-api <REVISION>
```

---

## Cloud Portability

- Same chart works on **kind**, **EKS**, **GKE**
- For private registries: configure `imagePullSecrets`
- Add **PodSecurity** (non-root, read-only FS) for hardened deployments