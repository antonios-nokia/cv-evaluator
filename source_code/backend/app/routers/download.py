from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from app.session_store import store
from app.services.pdf_generator import generate_cv_pdf, generate_cover_letter_pdf

DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

router = APIRouter()


@router.get("/session/{session_id}/download/{doc_type}")
async def download_document(session_id: str, doc_type: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if doc_type == "improved_cv":
        # DOCX path: return in-place edited bytes
        if session.improved_cv_bytes is not None:
            base = session.cv_filename.rsplit(".", 1)[0] if "." in session.cv_filename else session.cv_filename
            download_name = f"{base}_improved.docx"
            return Response(
                content=session.improved_cv_bytes,
                media_type=DOCX_CONTENT_TYPE,
                headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
            )

        # PDF fallback: generate from improved text
        cv_text = session.improved_cv_text or session.cv_text
        pdf_path = generate_cv_pdf(session_id, cv_text)
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename="improved_cv.pdf",
        )

    elif doc_type == "cover_letter":
        if not session.cover_letter_text:
            raise HTTPException(
                status_code=404,
                detail="Cover letter not generated yet. Call POST /session/{id}/cover-letter first.",
            )
        pdf_path = generate_cover_letter_pdf(session_id, session.cover_letter_text)
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename="cover_letter.pdf",
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown doc_type: {doc_type}. Use 'improved_cv' or 'cover_letter'.")
