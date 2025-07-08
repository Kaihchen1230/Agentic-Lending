from typing import Dict, Any, List
from datetime import datetime

# In-memory storage for chat sessions (in production, use a database)
chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_chat_session(chat_id: str) -> Dict[str, Any]:
    """Get or create a chat session"""
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = {
            "messages": [],
            "summaryData": None,
            "selectedRequestId": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    return chat_sessions[chat_id]

def update_chat_session(chat_id: str, messages: List[Dict], summary_data: Any = None, selected_request_id: str = ""):
    """Update a chat session with new data"""
    session = get_chat_session(chat_id)
    session["messages"] = messages
    session["updated_at"] = datetime.now().isoformat()
    if summary_data is not None:
        session["summaryData"] = summary_data
    if selected_request_id:
        session["selectedRequestId"] = selected_request_id
    chat_sessions[chat_id] = session