import logging
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models import UploadResponse
from app.session_store import store
from app.services.cv_parser import extract_cv_text

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # some browsers send this for DOCX
}
MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/upload", response_model=UploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a PDF or DOCX file.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB).")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    try:
        # Use the lowercased extension so .DOCX / .PDF also work
        normalized_filename = filename.rsplit(".", 1)[0] + ext
        cv_text = extract_cv_text(normalized_filename, file_bytes)
    except Exception as e:
        logger.error("Failed to parse uploaded file '%s': %s\n%s", filename, e, traceback.format_exc())
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    if not cv_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the file. Make sure it is not a scanned image or password-protected.")

    session = store.create(
        cv_text=cv_text,
        cv_filename=filename,
        cv_bytes=file_bytes if ext == ".docx" else None,
    )
    return UploadResponse(
        session_id=session.session_id,
        filename=filename,
        text_length=len(cv_text),
    )
