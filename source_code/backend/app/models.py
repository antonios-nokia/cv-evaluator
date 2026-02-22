from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    text_length: int


class JobDescriptionRequest(BaseModel):
    session_id: str
    text: Optional[str] = None
    url: Optional[str] = None


class JobDescriptionResponse(BaseModel):
    session_id: str
    job_text_length: int


class EvaluationRequest(BaseModel):
    session_id: str


class EvaluationResult(BaseModel):
    score: int
    strengths: list[str]
    gaps: list[str]
    summary: str


class EvaluationResponse(BaseModel):
    session_id: str
    evaluation: EvaluationResult


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    chat_history: list[ChatMessage]


class ImproveResponse(BaseModel):
    improved_score: int
    original_score: int
    score_delta: int
    evaluation: EvaluationResult


class CoverLetterResponse(BaseModel):
    cover_letter_text: str
