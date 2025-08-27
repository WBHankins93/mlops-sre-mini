# End-to-End Demo Runbook — mlops-sre-mini

This is a step-by-step runbook for local, Docker, Kubernetes, and GitHub Actions CI/CD.

---

## 0) Prerequisites

- Python 3.11
- Docker
- `kind`, `kubectl`, `helm`
- GitHub account + repo

---

## 1) Local training & serving

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r train/requirements.txt
python train/train.py
pip install -r app/requirements.txt
uvicorn app.main:app --port 8000 --reload
```

### Test (new terminal):

```bash
curl -s localhost:8000/healthz
curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"sepal_length":5.6,"sepal_width":3.0,"petal_length":4.1,"petal_width":1.3}'
curl -s localhost:8000/metrics | head -30
```

---

## 2) Docker

```bash
docker build -t iris-api:dev --build-arg MODEL_FILE=model.pkl .
docker run --rm -p 8000:8000 iris-api:dev
```

---

## 3) kind cluster + Prometheus/Grafana

```bash
kind create cluster --name mlops-sre-mini --config infra/kind/kind-config.yaml

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Load local image
kind load docker-image iris-api:dev --name mlops-sre-mini

# Deploy app
helm upgrade --install iris-api helm/iris-api \
  -n iris --create-namespace \
  --set image.repository=iris-api \
  --set image.tag=dev
```

### Verify:

```bash
kubectl -n iris get pods -w
kubectl -n iris port-forward svc/iris-api 8000:8000
curl -s localhost:8000/healthz
```

### Grafana:

```bash
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80
# Open http://localhost:3000 (admin / prom-operator)
# Import grafana/dashboards/iris-api.json
```

---

## 4) GitHub Actions CI/CD

### One-time setup:

1. **Repo → Settings → Actions → Workflow permissions → Read and write**
2. **Repo → Settings → Secrets → KUBECONFIG_B64** = base64 of kubeconfig (one line)

**macOS:**
```bash
base64 -i ~/.kube/config | tr -d '\n' | pbcopy
```

**Linux:**
```bash
base64 -w0 ~/.kube/config
```

### Pipelines:

- **Train** → trains and uploads artifact `model`
- **Build & Push** → pushes `ghcr.io/<owner>/iris-api:<sha>`
- **Deploy** → manual, uses `KUBECONFIG_B64` and `helm upgrade`

### Run end-to-end:

1. **Actions → Train → Run workflow**
2. **Build & Push** runs automatically; note SHA
3. **Actions → Deploy** → set `image_tag` = SHA

### Verify:

```bash
kubectl -n iris rollout status deploy/iris-api
```

---

## 5) Rollback

```bash
helm upgrade --install iris-api ./helm/iris-api \
  -n iris \
  --set image.repository=ghcr.io/<owner>/iris-api \
  --set image.tag=<PREVIOUS_SHA>
```

---

## 6) Cleanup

```bash
helm -n iris uninstall iris-api || true
helm -n monitoring uninstall monitoring || true
kind delete cluster --name mlops-sre-mini || true
```