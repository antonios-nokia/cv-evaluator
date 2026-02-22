# Source Code

Use this directory to make changes to the app and test locally before publishing new images to Docker Hub.

---

## Directory structure

```
source_code/
├── docker-compose.yml        ← builds and runs the app locally from source
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
    └── nginx.conf            ← editable (routing, headers, ports)
```

> **Frontend note:** Only the compiled output is available here, not the original TypeScript/React source.
> The only frontend file you can edit directly is `nginx.conf`.

---

## Step 1 — Set up `.env` (once)

```bash
cp ../.env.ollama.example .env
```

Or for OpenRouter:

```bash
cp ../.env.openrouter.example .env
# then open .env and fill in your OPENROUTER_API_KEY
```

---

## Step 2 — Edit the backend code

| File | Purpose |
|---|---|
| `backend/app/services/evaluator.py` | CV scoring prompt and logic |
| `backend/app/services/cv_improver.py` | DOCX in-place bullet insertion |
| `backend/app/services/cv_rewriter.py` | PDF CV rewriting |
| `backend/app/services/ollama_client.py` | LLM client |
| `backend/app/routers/` | API endpoints |
| `backend/app/session_store.py` | Session data model |
| `backend/requirements.txt` | Python dependencies |

---

## Step 3 — Build and run locally

```bash
cd source_code
docker compose up --build
```

Open the app at **http://localhost:5173**

Repeat steps 2 and 3 for every change.

---

## Step 4 — Push to Docker Hub when ready

```bash
docker login -u antoniosdim

docker tag cv-backend antoniosdim/cv-backend:latest
docker tag cv-frontend antoniosdim/cv-frontend:latest

docker push antoniosdim/cv-backend:latest
docker push antoniosdim/cv-frontend:latest
```

Others can then deploy the updated images using `docker-compose.hub.yml` from the repo root.
