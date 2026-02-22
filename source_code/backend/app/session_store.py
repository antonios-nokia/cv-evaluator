import time
import uuid
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Session:
    session_id: str
    cv_text: str
    cv_filename: str
    job_description: str = ""
    evaluation: Optional[dict] = None
    improved_cv_text: Optional[str] = None
    improved_evaluation: Optional[dict] = None
    cover_letter_text: Optional[str] = None
    chat_history: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    cv_bytes: Optional[bytes] = None
    improved_cv_bytes: Optional[bytes] = None

    def touch(self):
        self.updated_at = time.time()


class SessionStore:
    def __init__(self, ttl_seconds: int = 3600):
        self._sessions: dict[str, Session] = {}
        self.ttl_seconds = ttl_seconds

    def create(self, cv_text: str, cv_filename: str, cv_bytes: Optional[bytes] = None) -> Session:
        self._evict_expired()
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            cv_text=cv_text,
            cv_filename=cv_filename,
            cv_bytes=cv_bytes,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        self._evict_expired()
        return self._sessions.get(session_id)

    def delete(self, session_id: str):
        self._sessions.pop(session_id, None)

    def _evict_expired(self):
        now = time.time()
        expired = [
            sid
            for sid, s in self._sessions.items()
            if now - s.updated_at > self.ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]


from app.config import settings

store = SessionStore(ttl_seconds=settings.session_ttl_seconds)
