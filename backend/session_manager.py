sessions = {}

import uuid

def create_session():
    """Create a new chat session and return its UUID string."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return session_id


def get_session_context(session_id):
    """Get the stored message list for a session."""
    return sessions.get(session_id, [])


def append_message(session_id, message):
    """Append a message dict to the session's history."""
    sessions.setdefault(session_id, []).append(message)
