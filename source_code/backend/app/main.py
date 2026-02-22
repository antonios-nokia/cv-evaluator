from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, job, evaluate, chat, improve, cover_letter, download

app = FastAPI(title="CV Evaluator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(job.router)
app.include_router(evaluate.router)
app.include_router(chat.router)
app.include_router(improve.router)
app.include_router(cover_letter.router)
app.include_router(download.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
