# GitHub Repo & Registry Setup — mlops-sre-mini

## A) Create the repository

### Option A — GitHub CLI

```bash
gh repo create <OWNER>/mlops-sre-mini --private --source=. --push
# or use --public if you want it public
```

### Option B — GitHub UI

1. Open https://github.com/new → create repo named **mlops-sre-mini** (Private or Public)
2. Push your local repo:

```bash
git remote add origin https://github.com/<OWNER>/mlops-sre-mini.git
git branch -M dev
git push -u origin dev
```

---

## B) Actions permissions

- Repo → **Settings → Actions → General → Workflow permissions**
- Select **Read and write permissions** → Save

---

## C) Secret for Deploy workflow

- Repo → **Settings → Secrets and variables → Actions → New repository secret**
- **Name:** `KUBECONFIG_B64`
- **Value:** base64 of your kubeconfig as **one line**

**macOS:**
```bash
base64 -i ~/.kube/config | tr -d '\n' | pbcopy
```

**Linux:**
```bash
base64 -w0 ~/.kube/config | xclip -sel clip
```

---

## D) GitHub Container Registry (GHCR)

- The Build workflow pushes: `ghcr.io/<OWNER>/iris-api:<sha>`
- To allow public pulls: after first push → **Packages → iris-api → Package settings → Change visibility → Public**

---

## E) First pipeline run

1. Trigger **Train**: Actions → Train → Run workflow (or push changes in `train/**`)
2. Wait for **Build & Push** to publish the image. Note the SHA
3. Trigger **Deploy**: Actions → Deploy (manual Helm) → `image_tag` = SHA
4. Verify rollout:

```bash
kubectl -n iris get deploy,po,svc
kubectl -n iris rollout status deploy/iris-api
```