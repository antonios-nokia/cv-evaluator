import json
import httpx
from typing import AsyncGenerator

from app.config import settings


async def complete(prompt: str, system: str = "") -> str:
    """Send a prompt to Ollama and return the complete response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]


async def stream_tokens(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    """Stream tokens from Ollama as they are generated."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
