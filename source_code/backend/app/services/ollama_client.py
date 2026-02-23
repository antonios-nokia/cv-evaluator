"""
LLM client — supports Ollama and any OpenAI-compatible API (OpenRouter, OpenAI, etc.).
Provider is selected via the LLM_PROVIDER env var ("ollama" or "openai").
"""

import json
import httpx
from typing import AsyncGenerator

from app.config import settings


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

async def complete(prompt: str, system: str = "") -> str:
    """Return the full LLM response as a string."""
    if settings.llm_provider == "openai":
        return await _openai_complete(prompt, system)
    return await _ollama_complete(prompt, system)


async def stream_tokens(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    """Yield response tokens one by one."""
    if settings.llm_provider == "openai":
        async for token in _openai_stream(prompt, system):
            yield token
    else:
        async for token in _ollama_stream(prompt, system):
            yield token


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

def _ollama_messages(prompt: str, system: str) -> list:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


async def _ollama_complete(prompt: str, system: str) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": _ollama_messages(prompt, system),
                "stream": False,
                "options": {"num_predict": 2048},
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


async def _ollama_stream(prompt: str, system: str) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": _ollama_messages(prompt, system),
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


# ---------------------------------------------------------------------------
# OpenAI-compatible (OpenRouter, OpenAI, etc.)
# ---------------------------------------------------------------------------

def _openai_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if settings.openai_api_key:
        headers["Authorization"] = f"Bearer {settings.openai_api_key}"
    return headers


def _openai_messages(prompt: str, system: str) -> list:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


async def _openai_complete(prompt: str, system: str) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers=_openai_headers(),
            json={
                "model": settings.openai_model,
                "messages": _openai_messages(prompt, system),
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _openai_stream(prompt: str, system: str) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{settings.openai_base_url}/chat/completions",
            headers=_openai_headers(),
            json={
                "model": settings.openai_model,
                "messages": _openai_messages(prompt, system),
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    token = data["choices"][0].get("delta", {}).get("content", "")
                    if token:
                        yield token
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
