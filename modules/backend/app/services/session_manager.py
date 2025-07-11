import uuid
from typing import Dict, List


class SessionService:
    """Manage chat sessions and their message history."""

    def __init__(self) -> None:
        self.sessions: Dict[str, List[dict]] = {}

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id

    def get_session_context(self, session_id: str) -> List[dict]:
        """Retrieve message history for a session."""
        return self.sessions.get(session_id, [])

    def append_message(self, session_id: str, message: dict) -> None:
        """Append a message to the session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(message)

    def build_final_messages_for_grpc(
        self, query: str, context_docs: list[str], history: list[dict]
    ) -> list[dict]:
        """Construct the message list to send to the gRPC inference service."""
        final_messages: list[dict] = []
        if context_docs:
            context_str = "\n\n".join(context_docs)
            prompt = f"""
            请严格根据以下提供的上下文信息来精准、专业地回答用户的问题。
            请不要提及＜“根据上下文”或“根据提供的资料”这样的字眼，要让回答看起来就像是你自己的知识。
            如果上下文信息不足以回答问题，请直接回答“根据我掌握的知识，我无法回答这个问题”。

            【上下文信息】
            ---
            {context_str}
            ---
            """
            final_messages.append({"role": "system", "content": prompt.strip()})

        final_messages.extend(history)
        final_messages.append({"role": "user", "content": query})
        return final_messages


session_service = SessionService()
