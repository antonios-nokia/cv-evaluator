# CV Evaluator — Deployment Guide

## Files

- **`docker-compose.hub.yml`** — uses `antoniosdim/cv-backend` and `antoniosdim/cv-frontend` from Docker Hub, no build needed
- **`.env.ollama.example`** — copy to `.env` for local Ollama setup
- **`.env.openrouter.example`** — copy to `.env` for OpenRouter (coming soon)

## Prerequisites

- Docker + Docker Compose
- **Ollama** running on the host with `llama3.2` pulled:
  ```bash
  ollama serve
  ollama pull llama3.2
  ```

## Deploy

All three files must be in the same folder:

```
your-folder/
├── docker-compose.hub.yml
├── .env                ← copied and filled from one of the examples below
```

**Step 1 — Choose your LLM provider and create `.env`:**

```bash
# Option A: Ollama (local, no API key needed)
cp .env.ollama.example .env

# Option B: OpenRouter (cloud, requires API key)
cp .env.openrouter.example .env
# then edit .env and set your OPENROUTER_API_KEY
```

**Step 2 — Pull and start:**

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

**Step 3 — Open the app:**

```
http://localhost:5173
```

## Notes

- `.env` must be in the same directory as `docker-compose.hub.yml` — Docker Compose picks it up automatically
- No source code, Python, or Node.js needed on the host
- Session data is kept in memory with a 1-hour TTL (configurable via `SESSION_TTL_SECONDS`)
