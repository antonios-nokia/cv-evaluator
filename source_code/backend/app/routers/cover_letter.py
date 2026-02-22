from fastapi import APIRouter, HTTPException
from app.models import CoverLetterResponse
from app.session_store import store
from app.services import cover_letter as cl_service

router = APIRouter()


@router.post("/session/{session_id}/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not session.job_description:
        raise HTTPException(status_code=400, detail="Job description not set.")

    cv_text = session.improved_cv_text or session.cv_text

    cover_letter_text = await cl_service.generate_cover_letter(
        cv_text=cv_text,
        job_description=session.job_description,
    )

    session.cover_letter_text = cover_letter_text
    session.touch()

    return CoverLetterResponse(cover_letter_text=cover_letter_text)
