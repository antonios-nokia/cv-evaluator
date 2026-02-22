# Source Code

This directory contains the backend source code and compiled frontend output.
Use this if you need to modify the backend and rebuild the Docker image.

---

## Prerequisites

- Docker + Docker Compose
- Ollama running on the host (see `../DEPLOY.md` for setup)
- A Docker Hub account (to push your rebuilt image)

---

## Step 1 — Make your changes

Edit any files inside `backend/app/`. The main areas:

| Path | What it does |
|---|---|
| `backend/app/services/evaluator.py` | CV scoring logic |
| `backend/app/services/cv_improver.py` | DOCX in-place editing |
| `backend/app/services/cv_rewriter.py` | PDF CV rewriting |
| `backend/app/routers/` | API endpoints |
| `backend/app/session_store.py` | Session model |

---

## Step 2 — Rebuild the backend image

```bash
cd source_code/backend
docker build -t antoniosdim/cv-backend:latest .
```

---

## Step 3 — Push the new image to Docker Hub

```bash
docker login -u antoniosdim
docker push antoniosdim/cv-backend:latest
```

---

## Step 4 — Deploy

Go back to the root folder and deploy using the Hub compose file and your `.env`:

```bash
cd ..   # back to the repo root (where docker-compose.hub.yml is)

# Pick your .env if not already done
cp .env.ollama.example .env

# Pull the new backend image and restart
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

Open the app at **http://localhost:5173**

---

## Frontend note

`frontend_dist/` contains the **compiled output** (HTML/CSS/JS) extracted from the Docker image —
not the original TypeScript/React source files. The frontend can only be changed by modifying
the original source code and rebuilding with `npm run build`.
The `nginx.conf` file is the only frontend file that can be edited directly here.
