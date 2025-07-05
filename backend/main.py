import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agno.agent import Agent
from dotenv import load_dotenv
from agno.models.anthropic import Claude
from pydantic import BaseModel
import uvicorn
import json
import uuid
from datetime import datetime
from typing import List, Dict

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

# Create sessions directory
SESSIONS_DIR = os.path.join(BASEDIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

app = FastAPI(title="Agentic Lender Memo", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    session_id: str = None

class SessionMessage(BaseModel):
    id: str
    text: str
    sender: str  # 'user' or 'agent'
    timestamp: datetime

class ConversationSession(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[SessionMessage]
    status: str  # 'active', 'completed'

lending_memo_agent = Agent(
    model=Claude(id="claude-3-5-sonnet-20241022"),
    instructions=[
        "You are an expert credit analyst chatbot that guides underwriters through structured lending conversations.",
        "Your goal is to collect ALL required information for a complete credit memo, but be flexible with the order.",
        "",
        "REQUIRED SECTIONS TO COLLECT:",
        "1. CREDIT SUMMARY - Borrower profile, financial summary, key risks",
        "2. CONDITIONS & COVENANTS - Pre-funding conditions, ongoing covenants",
        "3. CLIENT BACKGROUND - Borrower details, guarantors, pledgers",
        "4. PRICING & FEES - Interest rates, fees, payment structure",
        "5. COLLATERAL ANALYSIS - Collateral details, LTV ratios, valuations",
        "6. OTHER INFORMATION - Regulatory considerations, exit plans, special notes",
        "",
        "CONVERSATION APPROACH:",
        "- Start with a friendly greeting and ask what information they'd like to provide first",
        "- Analyze what information the user provides and acknowledge it professionally",
        "- Identify which sections are still missing and ask for the most logical next piece",
        "- Be flexible - users may provide information in any order",
        "- Use natural follow-up questions based on what they've shared",
        "- Keep track of what's been provided and what's still needed",
        "",
        "EXAMPLE FOLLOW-UP PATTERNS:",
        "- If they provide borrower info, ask about collateral or financials next",
        "- If they mention a loan amount, ask about pricing or conditions",
        "- If they provide collateral details, ask about LTV or risk assessment",
        "- Always acknowledge what they've provided before asking for more",
        "",
        "IMPORTANT RULES:",
        "- Be conversational and professional, not robotic",
        "- Don't insist on a specific order - adapt to their flow",
        "- Only generate the final memo after collecting all 6 sections",
        "- If information is unclear, ask clarifying questions",
        "- Keep questions brief and focused",
        "- Thank them when they provide comprehensive information",
    ],
)

# Session management functions
def save_session(session: ConversationSession):
    session_file = os.path.join(SESSIONS_DIR, f"{session.session_id}.json")
    session_data = session.model_dump(default=str)  # Convert datetime to string
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

def load_session(session_id: str) -> ConversationSession:
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(session_file):
        return None
    
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    # Convert string timestamps back to datetime
    session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
    session_data["updated_at"] = datetime.fromisoformat(session_data["updated_at"])
    for msg in session_data["messages"]:
        msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
    
    return ConversationSession(**session_data)

def list_sessions() -> List[Dict]:
    sessions = []
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            session_id = filename[:-5]  # Remove .json extension
            session = load_session(session_id)
            if session:
                sessions.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "status": session.status,
                    "message_count": len(session.messages)
                })
    return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

@app.get("/")
async def root():
    return {"message": "Agentic Lender Memo API is running"}





# Session management endpoints
@app.post("/sessions")
async def create_session():
    session_id = str(uuid.uuid4())
    now = datetime.now()
    
    session = ConversationSession(
        session_id=session_id,
        title="New Credit Memo Conversation",
        created_at=now,
        updated_at=now,
        messages=[],
        status="active"
    )
    
    save_session(session)
    return {"session_id": session_id, "created_at": now}

@app.get("/sessions")
async def get_sessions():
    return {"sessions": list_sessions()}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = load_session(session_id)
    if not session:
        return {"error": "Session not found"}, 404
    return session

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(session_file):
        os.remove(session_file)
        return {"message": "Session deleted successfully"}
    return {"error": "Session not found"}, 404

@app.post("/chat")
async def chat_with_agent(chat_message: ChatMessage):
    # Get or create session
    session_id = chat_message.session_id
    if not session_id:
        # Create new session if none provided
        session_id = str(uuid.uuid4())
        now = datetime.now()
        session = ConversationSession(
            session_id=session_id,
            title="New Credit Memo Conversation",
            created_at=now,
            updated_at=now,
            messages=[],
            status="active"
        )
    else:
        session = load_session(session_id)
        if not session:
            return {"error": "Session not found"}, 404
    
    # Add user message to session
    user_message = SessionMessage(
        id=str(uuid.uuid4()),
        text=chat_message.message,
        sender="user",
        timestamp=datetime.now()
    )
    session.messages.append(user_message)
    
    # Get AI response
    response = lending_memo_agent.run(chat_message.message)
    
    # Add agent response to session
    agent_message = SessionMessage(
        id=str(uuid.uuid4()),
        text=response.content,
        sender="agent",
        timestamp=datetime.now()
    )
    session.messages.append(agent_message)
    
    # Update session title based on first user message
    if len(session.messages) == 2:  # First exchange
        session.title = chat_message.message[:50] + "..." if len(chat_message.message) > 50 else chat_message.message
    
    # Update session timestamp and save
    session.updated_at = datetime.now()
    save_session(session)
    
    return {
        "response": response.content,
        "session_id": session_id,
        "message_id": agent_message.id
    }

@app.post("/generate-summary")
async def generate_summary(chat_message: ChatMessage):
    # Get conversation from session if session_id provided
    if chat_message.session_id:
        session = load_session(chat_message.session_id)
        if session:
            # Use full conversation history
            conversation_text = "\n".join([f"{msg.sender}: {msg.text}" for msg in session.messages])
        else:
            conversation_text = chat_message.message
    else:
        conversation_text = chat_message.message
    
    # Check if conversation has enough content for a full memo
    has_sufficient_data = (
        len(conversation_text.split()) > 50 and  # At least 50 words
        any(keyword in conversation_text.lower() for keyword in ['borrower', 'loan', 'credit', 'collateral', 'income'])
    )
    
    if not has_sufficient_data:
        # Load HTML template from file
        template_path = os.path.join(os.path.dirname(__file__), "templates", "insufficient_data.html")
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return {"html_summary": html_content}
    
    # Generate full memo if sufficient data exists
    prompt = f"""
    Based on the following structured lending conversation, generate a comprehensive HTML credit memo that displays key lending data in a professional banking format.
    
    Conversation: {conversation_text}
    
    Create HTML that includes these sections with professional styling:
    1. EXECUTIVE SUMMARY - Brief overview with key metrics
    2. CREDIT SUMMARY - Borrower profile, financials, and collateral details
    3. CONDITIONS & COVENANTS - Pre-funding conditions and ongoing covenants
    4. CLIENT BACKGROUND - Borrower and guarantor information
    5. PRICING & FEES - Interest rate structure and fee schedule
    6. COLLATERAL ANALYSIS - Detailed collateral breakdown with LTV analysis
    7. RISK ASSESSMENT - Key risks and mitigating factors
    8. RECOMMENDATION - Final approval recommendation
    
    Use professional banking memo styling with:
    - Clean section headers with borders
    - Data tables for financial information
    - Color-coded risk indicators (green=low, yellow=medium, red=high)
    - Progress bars for LTV ratios
    - Professional color scheme (blues, grays, whites)
    - Card-based layout with proper spacing
    
    CRITICAL: Return ONLY the HTML content with inline CSS styling. Do NOT include any markdown formatting, code blocks, or ```html tags.
    Start directly with <div> and end with </div>. The HTML should be ready to inject into a React component using dangerouslySetInnerHTML.
    """
    
    response = lending_memo_agent.run(prompt)
    
    # Clean up any markdown formatting that might be added
    html_content = response.content
    if html_content.startswith('```html'):
        html_content = html_content[7:]  # Remove ```html
    if html_content.endswith('```'):
        html_content = html_content[:-3]  # Remove ```
    html_content = html_content.strip()
    
    return {"html_summary": html_content}

def main():
    print("Starting Agentic Lender Memo API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()