from fastapi import APIRouter, HTTPException
from app.models import ImproveResponse, EvaluationResult
from app.session_store import store
from app.services import cv_rewriter, cv_improver, evaluator

router = APIRouter()


@router.post("/session/{session_id}/improve", response_model=ImproveResponse)
async def improve_cv(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not session.job_description:
        raise HTTPException(status_code=400, detail="Job description not set.")

    original_score = (session.evaluation or {}).get("score", 0)

    if session.cv_bytes is not None:
        # DOCX path: edit in-place, preserve formatting
        improved_bytes, improved_text = await cv_improver.improve_docx(
            cv_bytes=session.cv_bytes,
            cv_text=session.cv_text,
            job_description=session.job_description,
            chat_history=session.chat_history,
        )
        session.improved_cv_bytes = improved_bytes
    else:
        # PDF / plain-text path: rewrite as text, generate PDF on download
        improved_text = await cv_rewriter.rewrite_cv(
            cv_text=session.cv_text,
            job_description=session.job_description,
            chat_history=session.chat_history,
        )

    new_eval = await evaluator.evaluate_cv(improved_text, session.job_description)

    session.improved_cv_text = improved_text
    session.improved_evaluation = new_eval
    session.touch()

    return ImproveResponse(
        improved_score=new_eval["score"],
        original_score=original_score,
        score_delta=new_eval["score"] - original_score,
        evaluation=EvaluationResult(**new_eval),
    )
