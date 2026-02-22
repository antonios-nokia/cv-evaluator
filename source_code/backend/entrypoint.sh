#!/bin/bash
set -e

OLLAMA_URL="${OLLAMA_URL:-http://host-gateway:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:latest}"

echo "Waiting for Ollama at ${OLLAMA_URL}..."
until curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; do
    echo "  Ollama not ready, retrying in 5s..."
    sleep 5
done
echo "Ollama is reachable."

# Check if model is already pulled
MODEL_NAME=$(echo "$OLLAMA_MODEL" | cut -d: -f1)
if curl -sf "${OLLAMA_URL}/api/tags" | grep -q "\"${OLLAMA_MODEL}\""; then
    echo "Model ${OLLAMA_MODEL} is already available."
else
    echo "Pulling model ${OLLAMA_MODEL} (this may take a while on first run)..."
    curl -sf -X POST "${OLLAMA_URL}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${OLLAMA_MODEL}\"}" \
        --no-buffer | while IFS= read -r line; do
            echo "$line"
        done
    echo "Model pull complete."
fi

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
