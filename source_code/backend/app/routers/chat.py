import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, ChatResponse, ChatMessage
from app.session_store import store
from app.services import ollama_client

router = APIRouter()

CHAT_SYSTEM = (
    "You are a helpful career advisor. The candidate has uploaded their CV and received an evaluation. "
    "Your job is to help them articulate skills and experience that are missing from their CV.\n\n"
    "For EVERY skill or experience the candidate mentions:\n"
    "1. Acknowledge it briefly\n"
    "2. Provide an EXACT bullet point sentence they can paste directly into their CV, formatted like:\n"
    "   📌 Add to [Section Name]: \"<ready-to-paste bullet point text>\"\n\n"
    "Keep your replies concise. Focus on producing ready-to-use CV sentences."
)

CHAT_PROMPT_TEMPLATE = """CV Evaluation:
Score: {score}/100
Gaps identified: {gaps}

Conversation so far:
{history}

Candidate: {message}

Respond with: a brief acknowledgement, then one or more ready-to-paste CV bullet points using the 📌 format."""


def _build_prompt(session, message: str) -> str:
    evaluation = session.evaluation or {}
    history_text = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in session.chat_history[-10:]
    )
    return CHAT_PROMPT_TEMPLATE.format(
        score=evaluation.get("score", "N/A"),
        gaps=", ".join(evaluation.get("gaps", [])),
        history=history_text or "None yet.",
        message=message,
    )


@router.post("/session/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, req: ChatRequest):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    prompt = _build_prompt(session, req.message)
    reply = await ollama_client.complete(prompt, system=CHAT_SYSTEM)

    session.chat_history.append({"role": "user", "content": req.message})
    session.chat_history.append({"role": "assistant", "content": reply})
    session.touch()

    return ChatResponse(
        reply=reply,
        chat_history=[ChatMessage(**m) for m in session.chat_history],
    )


@router.post("/session/{session_id}/chat/stream")
async def chat_stream(session_id: str, req: ChatRequest):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    prompt = _build_prompt(session, req.message)

    # Append user message immediately so history is correct if client disconnects
    session.chat_history.append({"role": "user", "content": req.message})
    session.touch()

    async def event_stream():
        tokens = []
        try:
            async for token in ollama_client.stream_tokens(prompt, system=CHAT_SYSTEM):
                tokens.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
        finally:
            reply = "".join(tokens)
            if reply:
                session.chat_history.append({"role": "assistant", "content": reply})
                session.touch()
            history = [{"role": m["role"], "content": m["content"]} for m in session.chat_history]
            yield f"data: {json.dumps({'done': True, 'chat_history': history})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
