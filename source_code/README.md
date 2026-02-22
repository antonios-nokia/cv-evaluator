# Source Code

## Backend (`backend/`)

Full Python source — all files needed to rebuild the backend image from scratch.

```
backend/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
└── app/
    ├── config.py
    ├── main.py
    ├── models.py
    ├── session_store.py
    ├── routers/
    │   ├── chat.py
    │   ├── cover_letter.py
    │   ├── download.py
    │   ├── evaluate.py
    │   ├── improve.py
    │   ├── job.py
    │   └── upload.py
    └── services/
        ├── cover_letter.py
        ├── cv_improver.py
        ├── cv_parser.py
        ├── cv_rewriter.py
        ├── evaluator.py
        ├── job_scraper.py
        ├── ollama_client.py
        └── pdf_generator.py
```

### Rebuild backend image

```bash
cd backend
docker build -t antoniosdim/cv-backend:latest .
docker push antoniosdim/cv-backend:latest
```

---

## Frontend (`frontend_dist/`)

> **Note:** This directory contains the **compiled output** (HTML/CSS/JS) extracted from the
> Docker image — not the original TypeScript/React source files.
> The compiled JS is minified and not directly editable.
>
> To make frontend changes you would need the original source files
> (src/, package.json, vite.config.ts, etc.) and rebuild with `npm run build`.

The nginx config (`nginx.conf`) is included and can be edited before rebuilding the frontend image.

---

## docker-compose.yml (build from source)

To build both images from source instead of pulling from Docker Hub:

```yaml
services:
  backend:
    build: ./source_code/backend
    container_name: cv-backend
    env_file: .env
    extra_hosts:
      - "host-gateway:host-gateway"
    volumes:
      - generated_docs:/tmp/cv_docs
    networks:
      - cv-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    image: antoniosdim/cv-frontend:latest
    container_name: cv-frontend
    ports:
      - "5173:80"
    networks:
      - cv-net
    depends_on:
      backend:
        condition: service_healthy

volumes:
  generated_docs:

networks:
  cv-net:
    driver: bridge
```

> The frontend service still uses the Docker Hub image since the TypeScript source is not available here.
> Only the backend can be rebuilt from source.
