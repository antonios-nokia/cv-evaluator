import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.models import EvaluationRequest, EvaluationResponse, EvaluationResult
from app.session_store import store
from app.services import evaluator, ollama_client
from app.services.evaluator import EVAL_SYSTEM, EVAL_PROMPT_TEMPLATE

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_cv(req: EvaluationRequest):
    session = store.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not session.job_description:
        raise HTTPException(status_code=400, detail="Job description not set.")

    try:
        result = await evaluator.evaluate_cv(session.cv_text, session.job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")
    session.evaluation = result
    session.touch()

    return EvaluationResponse(
        session_id=session.session_id,
        evaluation=EvaluationResult(**result),
    )


@router.get("/evaluate/stream")
async def evaluate_cv_stream(session_id: str = Query(...)):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not session.job_description:
        raise HTTPException(status_code=400, detail="Job description not set.")

    prompt = EVAL_PROMPT_TEMPLATE.format(
        cv_text=session.cv_text[:8000],
        job_description=session.job_description[:4000],
    )

    accumulated = []

    async def event_stream():
        nonlocal accumulated
        async for token in ollama_client.stream_tokens(prompt, system=EVAL_SYSTEM):
            accumulated.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Parse and store the evaluation once streaming is done
        full_text = "".join(accumulated)
        try:
            result = evaluator._parse_eval_json(full_text)
            result["score"] = max(0, min(100, int(result.get("score", 0))))
            session.evaluation = result
            session.touch()
            yield f"data: {json.dumps({'done': True, 'evaluation': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
