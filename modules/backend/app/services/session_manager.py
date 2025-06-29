import uuid
from typing import List, Dict

# Global in-memory storage for chat sessions
sessions: Dict[str, List[dict]] = {}

def create_session() -> str:
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return session_id

def get_session_context(session_id: str) -> List[dict]:
    """Retrieve message history for a session."""
    return sessions.get(session_id, [])

def append_message(session_id: str, message: dict):
    """Append a message to the session history."""
    if session_id not in sessions:
        sessions[session_id] = []
    sessions[session_id].append(message)
