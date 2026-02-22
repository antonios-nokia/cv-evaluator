# CV Evaluator — Deployment

## Requirements

- Docker + Docker Compose
- The three files below in the same folder:

```
your-folder/
├── docker-compose.hub.yml
├── .env.ollama.example
└── .env.openrouter.example
```

---

## Option A — Ollama (local, no API key)

Requires Ollama running on the host with `llama3.2` pulled:

```bash
ollama serve
ollama pull llama3.2
```

Copy the example and leave all values as-is:

```bash
cp .env.ollama.example .env
```

---

## Option B — OpenRouter (cloud, API key required)

No Ollama needed. Get your API key at https://openrouter.ai/keys

```bash
cp .env.openrouter.example .env
```

Then open `.env` and replace the placeholder with your real key:

```
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

Optionally change the model (browse models at https://openrouter.ai/models):

```
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet
```

---

## Start

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

Open the app at **http://localhost:5173**
