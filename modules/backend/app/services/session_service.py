import uuid
from typing import List, Dict


class SessionService:
    """Manage in-memory chat sessions."""

    def __init__(self) -> None:
        # session_id -> list of message dicts
        self.sessions: Dict[str, List[dict]] = {}

    def create_session(self) -> str:
        """Create a new chat session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id

    def get_session_context(self, session_id: str) -> List[dict]:
        """Return message history for a session."""
        return self.sessions.get(session_id, [])

    def append_message(self, session_id: str, message: dict) -> None:
        """Append a message to the given session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(message)


session_service = SessionService()
