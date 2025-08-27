# mlops-sre-mini

A compact, production-lean example showing **train → containerize → Helm deploy → Prometheus metrics → Grafana → CI/CD (GitHub Actions)**.

## Features

- ✅ Train a scikit-learn **LogisticRegression** on Iris → `model.pkl`
- ✅ FastAPI service: `GET /healthz`, `POST /predict`, `GET /metrics` (Prometheus)
- ✅ Docker image **bakes the model** for a hermetic MVP
- ✅ Helm chart (Deployment, Service, **ServiceMonitor**)
- ✅ Works on **kind** locally; same chart for **EKS/GKE**
- ✅ Starter **Grafana** dashboard (throughput, errors, p95 latency)
- ✅ CI/CD: **Train** (artifact) → **Build & Push** (GHCR) → **Deploy** (manual Helm)

---

## Prerequisites

- Python **3.11**
- Docker
- Kubernetes tooling: `kind`, `kubectl`, `helm`
- (Optional) GitHub CLI `gh` for quick repo creation

---

## Create the GitHub repo (one-time)

### Option A — GitHub CLI

```bash
# run from the project root (contains app/, train/, helm/, etc.)
gh repo create <OWNER>/mlops-sre-mini --private --source=. --push
# use --public if you want a public repo
```

### Option B — GitHub UI

1. Open https://github.com/new and create `mlops-sre-mini` (Private or Public)
2. Push your local repo:

```bash
git remote add origin https://github.com/<OWNER>/mlops-sre-mini.git
git branch -M dev
git push -u origin dev
```

---

## Local quick start

```bash
python3 -m venv .venv && source .venv/bin/activate

# 1) Train → writes model.pkl at repo root
pip install -r train/requirements.txt
python train/train.py

# 2) Serve locally
pip install -r app/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Smoke test (new terminal)

```bash
# Health
curl -s localhost:8000/healthz

# Predict
curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"sepal_length":5.6,"sepal_width":3.0,"petal_length":4.1,"petal_width":1.3}'

# Metrics (Prometheus text exposition)
curl -s localhost:8000/metrics | head -30
```

---

## Docker (model baked into the image)

```bash
docker build -t iris-api:dev --build-arg MODEL_FILE=model.pkl .
docker run --rm -p 8000:8000 iris-api:dev
```

**On Apple Silicon**, if you need AMD64:
```bash
docker buildx build --platform linux/amd64 -t iris-api:dev --build-arg MODEL_FILE=model.pkl .
```

---

## Kubernetes on kind (with Prometheus & Grafana)

```bash
# 1) Create cluster
kind create cluster --name mlops-sre-mini --config infra/kind/kind-config.yaml

# 2) Install kube-prometheus-stack (Prometheus + Grafana)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# 3) Load local image into kind to avoid pulling from a registry
kind load docker-image iris-api:dev --name mlops-sre-mini

# 4) Deploy via Helm (ServiceMonitor included)
helm upgrade --install iris-api helm/iris-api \
  -n iris --create-namespace \
  --set image.repository=iris-api \
  --set image.tag=dev
```

### Smoke test

```bash
kubectl -n iris get pods -w
kubectl -n iris port-forward svc/iris-api 8000:8000
curl -s localhost:8000/healthz
curl -s localhost:8000/metrics | head -30
```

---

## Grafana dashboard

```bash
# Port-forward Grafana
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80
```

1. Open http://localhost:3000 (default creds: `admin` / `prom-operator`)
2. Import `grafana/dashboards/iris-api.json`
3. If prompted, select your Prometheus datasource

### Generate traffic to populate panels

```bash
# with port-forward still up
for i in $(seq 1 50); do
  curl -s -X POST localhost:8000/predict \
    -H 'content-type: application/json' \
    -d '{"sepal_length":5.6,"sepal_width":3.0,"petal_length":4.1,"petal_width":1.3}' >/dev/null
done
```

---

## CI/CD (GitHub Actions)

### One-time repo settings

#### Actions permissions
**Repo → Settings → Actions → General → Workflow permissions** → select **Read and write permissions** → Save.

#### Secret for Deploy workflow (KUBECONFIG_B64)
**Repo → Settings → Secrets and variables → Actions → New repository secret**

- **Name:** `KUBECONFIG_B64`
- **Value:** your kubeconfig base64-encoded as one line.

**macOS:**
```bash
base64 -i ~/.kube/config | tr -d '\n' | pbcopy
```

**Linux:**
```bash
base64 -w0 ~/.kube/config | xclip -sel clip
```

#### GHCR visibility (optional)
After the first push of an image, make the `iris-api` package **Public** if you want unauthenticated pulls.

### Workflows included

#### Train (`.github/workflows/train.yml`)
Trains model and uploads artifact named `model`.

#### Build & Push (GHCR) (`.github/workflows/build.yml`)
Triggers on successful Train; downloads artifact; builds and pushes `ghcr.io/<owner>/iris-api:<sha>` (model baked in).

#### Deploy (manual Helm) (`.github/workflows/deploy.yml`)
`workflow_dispatch` with input `image_tag` (commit SHA). Decodes `KUBECONFIG_B64` and runs `helm upgrade`.

### Run the pipeline

1. **Actions → Train → Run workflow** (or push changes in `train/**`)
2. **Build & Push** runs automatically; note the image tag (commit SHA)
3. **Actions → Deploy (manual Helm)** → set `image_tag` to that SHA (and namespace if needed)

### Verify

```bash
kubectl -n iris get deploy,po,svc
kubectl -n iris rollout status deploy/iris-api
```

---

## Rollback by image SHA

```bash
helm upgrade --install iris-api ./helm/iris-api \
  -n iris \
  --set image.repository=ghcr.io/<owner>/iris-api \
  --set image.tag=<PREVIOUS_SHA>
```

---

## Cleanup

```bash
helm -n iris uninstall iris-api || true
helm -n monitoring uninstall monitoring || true
kind delete cluster --name mlops-sre-mini || true
```