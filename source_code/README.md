# Source Code — Rebuild & Deploy Guide

Use this directory when you need to modify the code and redeploy.
It has its own `docker-compose.yml` that builds both images locally from source.

---

## Directory structure

```
source_code/
├── docker-compose.yml        ← builds backend and frontend from source
├── backend/                  ← full Python source, fully editable
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
└── frontend_dist/            ← compiled JS/CSS/HTML + nginx config
    ├── Dockerfile
    ├── nginx.conf            ← editable
    └── assets/
```

> **Frontend note:** Only the compiled output is here, not the original TypeScript/React source.
> You can edit `nginx.conf` (routing, headers, ports). The JS/CSS files are minified and not editable.

---

## Prerequisites

- Docker + Docker Compose
- Ollama running on the host:
  ```bash
  ollama serve
  ollama pull llama3.2
  ```
- A `.env` file in this (`source_code/`) directory — copy from the root examples:
  ```bash
  cp ../.env.ollama.example .env        # Ollama
  # or
  cp ../.env.openrouter.example .env    # OpenRouter (fill in your API key)
  ```

---

## Step 1 — Edit the code

**Backend** — edit any file under `backend/app/`:

| File | Purpose |
|---|---|
| `backend/app/services/evaluator.py` | CV scoring prompt and logic |
| `backend/app/services/cv_improver.py` | DOCX in-place bullet insertion |
| `backend/app/services/cv_rewriter.py` | PDF CV rewriting |
| `backend/app/services/ollama_client.py` | LLM client |
| `backend/app/routers/` | API endpoints |
| `backend/app/session_store.py` | Session data model |
| `backend/requirements.txt` | Python dependencies |

**Frontend** — only `frontend_dist/nginx.conf` is editable here.

---

## Step 2 — Build and run locally from source

```bash
cd source_code
docker compose up --build
```

Open the app at **http://localhost:5173**

---

## Step 3 — Push new images to Docker Hub (optional)

Once satisfied with your changes, push the new images so others can deploy them via `docker-compose.hub.yml`:

```bash
docker login -u antoniosdim

docker tag cv-backend antoniosdim/cv-backend:latest
docker tag cv-frontend antoniosdim/cv-frontend:latest

docker push antoniosdim/cv-backend:latest
docker push antoniosdim/cv-frontend:latest
```

Others can then pull and run the updated images using the root `docker-compose.hub.yml` as usual.

---

## Quick reference

| Task | Command |
|---|---|
| Build and start from source | `cd source_code && docker compose up --build` |
| Stop | `docker compose down` |
| View logs | `docker compose logs -f` |
| Push backend to Docker Hub | `docker tag cv-backend antoniosdim/cv-backend:latest && docker push antoniosdim/cv-backend:latest` |
| Push frontend to Docker Hub | `docker tag cv-frontend antoniosdim/cv-frontend:latest && docker push antoniosdim/cv-frontend:latest` |
