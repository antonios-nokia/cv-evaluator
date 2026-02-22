from fastapi import APIRouter, HTTPException
from app.models import JobDescriptionRequest, JobDescriptionResponse
from app.session_store import store
from app.services.job_scraper import scrape_job_from_url

router = APIRouter()


@router.post("/job-description", response_model=JobDescriptionResponse)
async def set_job_description(req: JobDescriptionRequest):
    session = store.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if req.url:
        try:
            job_text = scrape_job_from_url(req.url)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not scrape URL: {e}")
    elif req.text:
        job_text = req.text.strip()
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'url'.")

    if not job_text:
        raise HTTPException(status_code=422, detail="Job description is empty.")

    session.job_description = job_text
    session.touch()

    return JobDescriptionResponse(
        session_id=session.session_id,
        job_text_length=len(job_text),
    )
