# Source Code — Rebuild & Deploy Guide

This directory contains the backend source and compiled frontend output.
Use this when you need to modify the code and publish new Docker images.

---

## Directory structure

```
source_code/
├── backend/                  ← Full Python source, fully editable
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── app/
│       ├── config.py
│       ├── main.py
│       ├── models.py
│       ├── session_store.py
│       ├── routers/          ← API endpoints
│       └── services/         ← AI logic (evaluator, improver, rewriter...)
└── frontend_dist/            ← Compiled JS/CSS/HTML (not editable TypeScript source)
    ├── nginx.conf            ← Nginx config (editable)
    └── assets/
```

> **Frontend note:** Only the compiled output is available here, not the original
> TypeScript/React source. The JS files are minified and cannot be edited directly.
> To modify the frontend UI you would need the original source files.

---

## Prerequisites

- Docker + Docker Compose
- Docker Hub account (`antoniosdim`)
- Ollama running on the host:
  ```bash
  ollama serve
  ollama pull llama3.2
  ```

---

## Backend — modify, rebuild, push

**Step 1 — Edit backend files**

The main files to change:

| File | Purpose |
|---|---|
| `backend/app/services/evaluator.py` | CV scoring prompt and logic |
| `backend/app/services/cv_improver.py` | DOCX in-place bullet insertion |
| `backend/app/services/cv_rewriter.py` | PDF CV rewriting |
| `backend/app/services/ollama_client.py` | LLM client (Ollama / OpenRouter) |
| `backend/app/routers/` | API endpoints |
| `backend/app/session_store.py` | Session data model |
| `backend/requirements.txt` | Python dependencies |

**Step 2 — Build the backend image**

```bash
cd source_code/backend
docker build -t antoniosdim/cv-backend:latest .
```

**Step 3 — Push to Docker Hub**

```bash
docker login -u antoniosdim
docker push antoniosdim/cv-backend:latest
```

---

## Frontend — rebuild and push (nginx config only)

If you only need to change `nginx.conf` (routing, headers, ports):

**Step 1 — Edit `frontend_dist/nginx.conf`**

**Step 2 — Create a minimal Dockerfile**

```bash
cat > source_code/frontend_dist/Dockerfile <<'EOF'
FROM nginx:1.27-alpine
COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EOF
```

**Step 3 — Build and push the frontend image**

```bash
cd source_code/frontend_dist
docker build -t antoniosdim/cv-frontend:latest .
docker login -u antoniosdim
docker push antoniosdim/cv-frontend:latest
```

---

## Deploy after rebuilding

Once your new images are pushed to Docker Hub, deploy from the repo root:

```bash
cd ..   # repo root, where docker-compose.hub.yml lives

# Set up .env if not already done
cp .env.ollama.example .env      # or .env.openrouter.example

# Pull the updated images and restart
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

Open the app at **http://localhost:5173**

---

## Quick reference

| Task | Command |
|---|---|
| Rebuild backend | `cd source_code/backend && docker build -t antoniosdim/cv-backend:latest .` |
| Rebuild frontend | `cd source_code/frontend_dist && docker build -t antoniosdim/cv-frontend:latest .` |
| Push both | `docker push antoniosdim/cv-backend:latest && docker push antoniosdim/cv-frontend:latest` |
| Deploy | `docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d` |
| Check logs | `docker compose -f docker-compose.hub.yml logs -f` |
| Stop | `docker compose -f docker-compose.hub.yml down` |
