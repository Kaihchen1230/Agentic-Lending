from fastapi import APIRouter, HTTPException
from typing import List
import os
import re
import random
from datetime import datetime

from ..models import ChatMessage, CreditRequest, DetailedCreditRequest
from ..memory import get_chat_session, update_chat_session, chat_sessions
from ..agents import fast_chat_agent, summary_generation_agent
from ..services import fetch_credit_request_details
from ..services.mock_data_service import get_mock_credit_requests, get_mock_detailed_credit_request

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Agentic Lender Memo API is running"}

@router.get("/chat-history/{chat_id}")
async def get_chat_history(chat_id: str):
    """Get chat history for a specific chat ID"""
    if chat_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[chat_id]
    return {
        "chatId": chat_id,
        "messages": session["messages"],
        "summaryData": session["summaryData"],
        "selectedRequestId": session["selectedRequestId"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"]
    }

@router.get("/credit-requests")
async def get_credit_requests() -> List[CreditRequest]:
    """Get list of credit requests"""
    return get_mock_credit_requests()

@router.get("/credit-requests/{request_id}")
async def get_credit_request_details(request_id: str) -> DetailedCreditRequest:
    """Get detailed credit request information"""
    return get_mock_detailed_credit_request(request_id)

@router.post("/chat")
async def chat_with_agent(chat_message: ChatMessage):
    """Chat with the AI agent"""
    # Get chat session (create if doesn't exist)
    chat_id = chat_message.chatId or f"chat_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
    session = get_chat_session(chat_id)
    
    # Create new message
    new_message = {
        "id": f"msg_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
        "text": chat_message.message,
        "sender": "user",
        "timestamp": datetime.now().isoformat()
    }
    
    # Add user message to session
    session["messages"].append(new_message)
    
    # Check if the message contains a credit request ID
    request_id_pattern = r"US-\d{6}-\d{4}"
    request_id_match = re.search(request_id_pattern, chat_message.message)
    
    if request_id_match:
        request_id = request_id_match.group(0)
        print(f"Credit request ID detected: {request_id}")
        
        # Fetch detailed credit request information
        credit_details = await fetch_credit_request_details(request_id)
        
        # Create a concise message for fast chat response
        enhanced_message = f"""
User asked: {chat_message.message}

Credit request for {request_id} has been retrieved. Key details:
- Borrower: Available in data
- Status: Ready for analysis
- Summary: Will be generated automatically

Provide a quick, friendly acknowledgment (1-3 sentences max) that you've got their request and direct them to check the summary section for details.
"""
        
        # Get fast AI response from single chat agent
        response = fast_chat_agent.run(enhanced_message)
        
        # If we have credit request data, also generate the HTML summary
        print(f"Generating HTML summary for: {request_id}")
        
        # Generate HTML summary using the Credit Memo Specialist
        summary_prompt = f"""
        Based on the following credit request data, generate a comprehensive HTML credit memo that displays key lending data in a professional banking format.
        
        CREDIT REQUEST DATA:
        {credit_details}
        
        Create a comprehensive HTML credit memo with these sections:
        - EXECUTIVE SUMMARY - Brief overview with key metrics
        - CREDIT SUMMARY - Borrower profile, financials, and collateral details
        - CONDITIONS & COVENANTS - Pre-funding conditions and ongoing covenants
        - CLIENT BACKGROUND - Borrower and guarantor information
        - PRICING & FEES - Interest rate structure and fee schedule
        - COLLATERAL ANALYSIS - Detailed collateral breakdown with LTV analysis
        - RISK ASSESSMENT - Key risks and mitigating factors
        - RECOMMENDATION - Final approval recommendation
        
        Use professional banking memo styling with:
        - Clean section headers with borders
        - Data tables for financial information
        - Color-coded risk indicators (green=low, yellow=medium, red=high)
        - Progress bars for LTV ratios
        - Professional color scheme (blues, grays, whites)
        - Card-based layout with proper spacing
        - Consistent typography: font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
        - Main container background: #f8fafc
        - Card styling: white background, border-radius: 12px, box-shadow: 0 2px 10px rgba(0,0,0,0.1)
        - For incomplete sections: add clickable-section class with data-section attribute and hover effects
        
        CRITICAL: Return ONLY the HTML content with inline CSS styling. Do NOT include any markdown formatting, code blocks, or ```html tags.
        Start directly with <div> and end with </div>. The HTML should be ready to inject into a React component using dangerouslySetInnerHTML.
        """
        
        # Generate HTML summary
        summary_response = summary_generation_agent.run(summary_prompt)
        
        # Clean up any markdown formatting
        html_content = summary_response.content
        if html_content.startswith('```html'):
            html_content = html_content[7:]  # Remove ```html
        if html_content.endswith('```'):
            html_content = html_content[:-3]  # Remove ```
        html_content = html_content.strip()
        
        # Create agent response message
        agent_message = {
            "id": f"msg_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
            "text": response.content,
            "sender": "agent",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add agent message to session
        session["messages"].append(agent_message)
        
        # Delay summary update to show after chatbot response
        # Update summary data
        summary_data = {
            "lastQuery": chat_message.message,
            "lastResponse": response.content,
            "timestamp": datetime.now().isoformat(),
            "htmlSummary": html_content,
            "creditRequestId": request_id,
            "summaryGenerated": True
        }
        
        # Update session with new data
        update_chat_session(chat_id, session["messages"], summary_data, request_id)
        
        return {
            "response": response.content,
            "team_mode": "fast_single_agent",
            "agents_used": [fast_chat_agent.name],
            "html_summary": html_content,
            "credit_request_id": request_id,
            "summary_generated": True,
            "chatId": chat_id
        }
    else:
        # Handle general messages without credit request ID
        general_message = f"""
User message: {chat_message.message}

Provide a quick, helpful response (1-3 sentences max). Be conversational and ask clarifying questions if needed.
"""
        
        # Get fast AI response for general conversation
        response = fast_chat_agent.run(general_message)
        
        # Create agent response message
        agent_message = {
            "id": f"msg_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
            "text": response.content,
            "sender": "agent",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add agent message to session
        session["messages"].append(agent_message)
        
        # Update summary data
        summary_data = {
            "lastQuery": chat_message.message,
            "lastResponse": response.content,
            "timestamp": datetime.now().isoformat(),
            "summaryGenerated": False
        }
        
        # Update session with new data
        update_chat_session(chat_id, session["messages"], summary_data)
        
        return {
            "response": response.content,
            "team_mode": "fast_single_agent",
            "agents_used": [fast_chat_agent.name],
            "summary_generated": False,
            "chatId": chat_id
        }

@router.post("/generate-summary")
async def generate_summary(chat_message: ChatMessage):
    """Generate summary from conversation"""
    # Use the provided message text for summary generation
    conversation_text = chat_message.message
    
    # Check if conversation has enough content for a full memo
    has_sufficient_data = (
        len(conversation_text.split()) > 50 and  # At least 50 words
        any(keyword in conversation_text.lower() for keyword in ['borrower', 'loan', 'credit', 'collateral', 'income'])
    )
    
    if not has_sufficient_data:
        # Load HTML template from file
        template_path = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "insufficient_data.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except FileNotFoundError:
            html_content = "<div>Insufficient data for summary generation</div>"
        return {"html_summary": html_content}
    
    # Generate full memo using the dedicated Credit Memo Specialist directly
    prompt = f"""
    Based on the following structured lending conversation, generate a comprehensive HTML credit memo that displays key lending data in a professional banking format.
    
    Conversation: {conversation_text}
    
    Create a comprehensive HTML credit memo with these sections:
    - EXECUTIVE SUMMARY - Brief overview with key metrics
    - CREDIT SUMMARY - Borrower profile, financials, and collateral details
    - CONDITIONS & COVENANTS - Pre-funding conditions and ongoing covenants
    - CLIENT BACKGROUND - Borrower and guarantor information
    - PRICING & FEES - Interest rate structure and fee schedule
    - COLLATERAL ANALYSIS - Detailed collateral breakdown with LTV analysis
    - RISK ASSESSMENT - Key risks and mitigating factors
    - RECOMMENDATION - Final approval recommendation
    
    Use professional banking memo styling with:
    - Clean section headers with borders
    - Data tables for financial information
    - Color-coded risk indicators (green=low, yellow=medium, red=high)
    - Progress bars for LTV ratios
    - Professional color scheme (blues, grays, whites)
    - Card-based layout with proper spacing
    - Consistent typography: font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
    - Main container background: #f8fafc
    - Card styling: white background, border-radius: 12px, box-shadow: 0 2px 10px rgba(0,0,0,0.1)
    - For incomplete sections: add clickable-section class with data-section attribute and hover effects
    
    CRITICAL: Return ONLY the HTML content with inline CSS styling. Do NOT include any markdown formatting, code blocks, or ```html tags.
    Start directly with <div> and end with </div>. The HTML should be ready to inject into a React component using dangerouslySetInnerHTML.
    """
    
    # Use the Credit Memo Specialist directly to avoid team coordination text
    response = summary_generation_agent.run(prompt)
    
    # Clean up any markdown formatting that might be added
    html_content = response.content
    if html_content.startswith('```html'):
        html_content = html_content[7:]  # Remove ```html
    if html_content.endswith('```'):
        html_content = html_content[:-3]  # Remove ```
    html_content = html_content.strip()
    
    return {
        "html_summary": html_content,
        "generated_by": "credit-memo-specialist",
        "agents_used": [summary_generation_agent.name]
    }

@router.post("/generate-credit-memo")
async def generate_credit_memo(chat_message: ChatMessage):
    """
    Generate an HTML credit memo based on a credit request ID.
    This endpoint specifically handles credit request ID analysis and generates detailed HTML memos.
    """
    # Check if the message contains a credit request ID
    request_id_pattern = r"US-\d{6}-\d{4}"
    request_id_match = re.search(request_id_pattern, chat_message.message)
    
    if not request_id_match:
        return {
            "error": "No credit request ID found in message. Please provide a valid credit request ID.",
            "html_summary": "<div style='padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px;'><h3 style='color: #dc3545; margin: 0;'>Error</h3><p style='margin: 10px 0 0 0;'>Please provide a valid credit request ID (format: US-XXXXXX-YYYY) to generate a credit memo.</p></div>"
        }
    
    request_id = request_id_match.group(0)
    print(f"Generating HTML credit memo for: {request_id}")
    
    # Fetch detailed credit request information
    credit_details = await fetch_credit_request_details(request_id)
    
    # Create detailed prompt for HTML memo generation
    memo_prompt = f"""
Generate a comprehensive HTML credit memo for credit request {request_id}.

CREDIT REQUEST DATA:
{credit_details}

Generate a comprehensive HTML credit memo with these sections:
- EXECUTIVE SUMMARY - Key metrics, recommendation summary, loan overview
- CREDIT SUMMARY - Borrower financial profile, risk assessment, creditworthiness
- CLIENT BACKGROUND - Borrower details, employment history, guarantors
- COLLATERAL ANALYSIS - Property valuation, LTV analysis, market conditions
- PRICING & FEES - Interest rate justification, fee structure, payment analysis
- CONDITIONS & COVENANTS - Pre-funding conditions, ongoing requirements
- RISK ASSESSMENT - Key risks, mitigating factors, overall risk rating
- RECOMMENDATION - Final lending decision with supporting rationale

CRITICAL HTML FORMATTING REQUIREMENTS:
- Generate ONLY HTML content with inline CSS styling
- Use professional banking memo design with clean sections
- Include data tables for financial information
- Use color-coded risk indicators (green=low, yellow=medium, red=high)
- Add progress bars for LTV ratios and key metrics
- Professional color scheme (blues, grays, whites)
- Card-based layout with proper spacing and borders
- Consistent typography: font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- Main container background: #f8fafc
- Card styling: white background, border-radius: 12px, box-shadow: 0 2px 10px rgba(0,0,0,0.1)
- For incomplete sections: add clickable-section class with data-section attribute and hover effects
- Make it visually appealing and easy to read
- Do NOT include any markdown, code blocks, or ```html tags
- Start with <div> and end with </div>
- Ready for React dangerouslySetInnerHTML injection

Focus on creating a professional, comprehensive, and visually appealing credit memo.
"""
    
    # Generate HTML memo using summary generation agent
    response = summary_generation_agent.run(memo_prompt)
    
    # Clean up any markdown formatting that might be added
    html_content = response.content
    if html_content.startswith('```html'):
        html_content = html_content[7:]  # Remove ```html
    if html_content.endswith('```'):
        html_content = html_content[:-3]  # Remove ```
    html_content = html_content.strip()
    
    return {
        "html_summary": html_content,
        "credit_request_id": request_id,
        "generated_by": "credit-memo-specialist",
        "agents_used": [summary_generation_agent.name],
        "memo_type": "comprehensive_credit_analysis"
    }