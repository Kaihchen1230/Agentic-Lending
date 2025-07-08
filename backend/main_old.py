import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agno.agent import Agent
from agno.team.team import Team
from dotenv import load_dotenv
from agno.models.anthropic import Claude
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Dict, Any
import random
import json
import httpx
import re
from datetime import datetime

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))

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

def get_conditions_for_borrower(borrower_key: str) -> List[str]:
    """Get conditions based on borrower's missing data"""
    if borrower_key == "robert":
        return [
            "Complete credit application required",
            "Income verification needed",
            "Employment history documentation required",
            "Asset and liability statements needed",
            "Property appraisal pending",
            "Complete financial documentation required"
        ]
    elif borrower_key == "sarah":
        return [
            "Credit score verification required",
            "Debt-to-income ratio calculation needed",
            "Asset documentation required",
            "Property appraisal completion",
            "Clear title search"
        ]
    elif borrower_key == "michael":
        return [
            "Income verification required",
            "Employment history documentation needed",
            "Property appraisal completion",
            "Clear title search",
            "Homeowner's insurance policy"
        ]
    elif borrower_key == "emily":
        return [
            "Liability statement required",
            "Property appraisal completion",
            "Clear title search",
            "Homeowner's insurance policy"
        ]
    else:
        return [
            "Property appraisal completion",
            "Clear title search",
            "Homeowner's insurance policy",
            "Final underwriting review"
        ]

def get_covenants_for_borrower(borrower_key: str) -> List[str]:
    """Get covenants based on borrower profile"""
    if borrower_key == "robert":
        return ["Covenants to be determined upon completion of application"]
    else:
        return [
            "Maintain property insurance",
            "Pay property taxes timely",
            "Notify lender of address changes",
            "Maintain property in good condition"
        ]

def get_guarantors_for_borrower(borrower_key: str) -> List[str]:
    """Get guarantors based on borrower profile"""
    if borrower_key in ["robert", "sarah"]:
        return ["Guarantor information pending"]
    elif borrower_key == "michael":
        return ["Co-signer may be required"]
    else:
        return []

def get_regulatory_notes_for_borrower(borrower_key: str) -> str:
    """Get regulatory notes based on borrower profile"""
    if borrower_key == "robert":
        return "Regulatory compliance review pending - incomplete application"
    elif borrower_key in ["sarah", "michael"]:
        return "TRID and QM compliance review in progress"
    else:
        return "Complies with TRID and QM requirements"

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
    chatId: Optional[str] = None

class CreditRequest(BaseModel):
    request_id: str
    borrower_name: str
    loan_amount: float
    status: str

class CollateralInfo(BaseModel):
    property_type: str
    property_value: float
    ltv_ratio: float
    appraisal_date: str
    address: str

class BorrowerInfo(BaseModel):
    name: str
    credit_score: int
    annual_income: float
    debt_to_income_ratio: float
    employment_history: str
    assets: float
    liabilities: float

class PricingInfo(BaseModel):
    interest_rate: float
    loan_term_months: int
    monthly_payment: float
    origination_fee: float
    processing_fee: float
    total_fees: float

class DetailedCreditRequest(BaseModel):
    request_id: str
    borrower: BorrowerInfo
    collateral: CollateralInfo
    pricing: PricingInfo
    loan_amount: float
    loan_purpose: str
    status: str
    risk_rating: str
    conditions: List[str]
    covenants: List[str]
    guarantors: List[str]
    regulatory_notes: str
    created_date: str
    updated_date: str


# Fast Chat Agent for Quick Responses
fast_chat_agent = Agent(
    name="Quick Chat Assistant",
    role="Provides fast, helpful conversational responses about lending",
    model=Claude(id="claude-3-5-sonnet-20241022"),
    instructions=[
        "You are a quick chat assistant for lending. Keep responses to 1-3 sentences maximum.",
        "Be friendly, acknowledge requests briefly, and direct users to the summary section for details.",
        "Examples: 'Got it! Check the summary for analysis.' or 'I can help! What aspect interests you?'"
    ],
    markdown=True,
)

# Summary Generation Agent - Specialized in creating detailed credit memos (used separately for summaries)
summary_generation_agent = Agent(
    name="Credit Memo Specialist", 
    role="Generates comprehensive credit memos and lending recommendations",
    model=Claude(id="claude-3-5-sonnet-20241022"),
    instructions=[
        "You are a specialized Credit Memo Specialist responsible for creating comprehensive lending analysis and recommendations.",
        "",
        "YOUR PRIMARY RESPONSIBILITIES:",
        "- Create structured credit memos based on processed credit data",
        "- Provide risk assessments and lending recommendations",
        "- Generate professional banking documentation",
        "- Ensure compliance with lending standards and regulations",
        "",
        "CREDIT MEMO SECTIONS TO GENERATE:",
        "1. EXECUTIVE SUMMARY - Key metrics, recommendation, loan summary",
        "2. CREDIT SUMMARY - Borrower profile, financial analysis, risk assessment",
        "3. CLIENT BACKGROUND - Borrower details, employment, guarantors",
        "4. COLLATERAL ANALYSIS - Property valuation, LTV analysis, market assessment",
        "5. PRICING & FEES - Rate justification, fee structure, payment analysis", 
        "6. CONDITIONS & COVENANTS - Pre-funding conditions, ongoing requirements",
        "7. RISK ASSESSMENT - Key risks, mitigating factors, overall rating",
        "8. RECOMMENDATION - Final decision with supporting rationale",
        "",
        "ANALYSIS APPROACH:",
        "- Use processed credit data to make informed lending decisions",
        "- Reference specific metrics and ratios in your analysis",
        "- Explain the reasoning behind risk ratings and recommendations",
        "- Consider market conditions and regulatory requirements",
        "- Provide actionable next steps and conditions",
        "",
        "HTML MEMO FORMATTING:",
        "- Generate ONLY HTML content with inline CSS styling",
        "- Use professional banking language and format",
        "- Include specific data points and calculations in HTML tables",
        "- Organize information in clear, logical HTML sections",
        "- Use color-coded risk indicators (green=low, yellow=medium, red=high)",
        "- Include progress bars for LTV ratios and other metrics",
        "- Use professional color scheme (blues, grays, whites)",
        "- Create card-based layout with proper spacing",
        "- Highlight key risks and mitigating factors",
        "- Provide clear, actionable recommendations",
        "",
        "CONSISTENT STYLING REQUIREMENTS:",
        "- Use font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "- Background color: #f8fafc for main container",
        "- Card background: white with border-radius: 12px",
        "- Box shadow: 0 2px 10px rgba(0,0,0,0.1)",
        "- Header gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "- Section headers: color: #1e293b, font-size: 18px, font-weight: 600",
        "- For incomplete sections, add clickable-section class with data-section attribute",
        "- Clickable sections should have cursor: pointer and hover effects",
        "- Use consistent spacing: padding: 24px for cards, margin-bottom: 24px between sections",
        "",
        "IMPORTANT GUIDELINES:",
        "- Base all recommendations on actual credit data provided",
        "- Explain rationale for all lending decisions",
        "- Consider regulatory compliance (TRID, QM, fair lending)",
        "- Be thorough but concise in your analysis",
        "- Provide professional-grade credit memo documentation",
        "",
        "CRITICAL HTML OUTPUT REQUIREMENTS:",
        "- Return ONLY HTML content with inline CSS styling",
        "- Do NOT include any markdown formatting, code blocks, or ```html tags",
        "- Do NOT include any explanatory text, coordination messages, or agent communication",
        "- Start directly with <div> and end with </div>",
        "- The HTML should be ready to inject into a React component using dangerouslySetInnerHTML",
        "- Always generate HTML, never plain text for credit memos",
        "- Your entire response should be pure HTML code, nothing else",
        "",
        "CLICKABLE SECTIONS FOR INCOMPLETE DATA:",
        "- If a section is incomplete or needs more information, make it clickable",
        "- Add class='clickable-section' and data-section='Section Name' attributes",
        "- Include hover effects and cursor pointer styling",
        "- Use visual indicators (different background colors) for incomplete sections",
        "- Example: <div class='clickable-section' data-section='Risk Assessment' style='cursor: pointer; background: #fef3c7; border-left: 4px solid #f59e0b;' onmouseover='this.style.background=\"#fde68a\"' onmouseout='this.style.background=\"#fef3c7\"'>",
    ],
)

# For summary generation, we'll use the summary_generation_agent directly
# This is faster than using a team and produces the same quality results


@app.get("/")
async def root():
    return {"message": "Agentic Lender Memo API is running"}

@app.get("/chat-history/{chat_id}")
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

@app.get("/credit-requests")
async def get_credit_requests() -> List[CreditRequest]:
    # Mock external API call - in real implementation, this would fetch from an external service
    # For demonstration, we'll generate some sample credit requests
    sample_requests = [
        CreditRequest(
            request_id=f"US-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}",
            borrower_name="John Smith",
            loan_amount=250000.0,
            status="pending"
        ),
        CreditRequest(
            request_id=f"US-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}",
            borrower_name="Sarah Johnson",
            loan_amount=450000.0,
            status="under_review"
        ),
        CreditRequest(
            request_id=f"US-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}",
            borrower_name="Michael Brown",
            loan_amount=180000.0,
            status="pending"
        ),
        CreditRequest(
            request_id=f"US-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}",
            borrower_name="Emily Davis",
            loan_amount=320000.0,
            status="approved"
        ),
        CreditRequest(
            request_id=f"US-{random.randint(100000, 999999)}-{random.randint(1000, 9999)}",
            borrower_name="Robert Wilson",
            loan_amount=275000.0,
            status="pending"
        )
    ]
    
    return sample_requests

@app.get("/credit-requests/{request_id}")
async def get_credit_request_details(request_id: str) -> DetailedCreditRequest:
    # Mock external API call - in real implementation, this would fetch from an external service
    # Generate mock detailed data based on request_id
    
    # Sample borrower data with missing information for testing
    borrowers = {
        "john": BorrowerInfo(
            name="John Smith",
            credit_score=750,
            annual_income=85000.0,
            debt_to_income_ratio=0.28,
            employment_history="Software Engineer at TechCorp for 5 years",
            assets=150000.0,
            liabilities=45000.0
        ),
        "sarah": BorrowerInfo(
            name="Sarah Johnson",
            credit_score=0,  # Missing credit score
            annual_income=95000.0,
            debt_to_income_ratio=0.0,  # Missing DTI ratio
            employment_history="Marketing Director at AdCorp for 3 years",
            assets=0.0,  # Missing asset information
            liabilities=60000.0
        ),
        "michael": BorrowerInfo(
            name="Michael Brown",
            credit_score=680,
            annual_income=0.0,  # Missing income verification
            debt_to_income_ratio=0.35,
            employment_history="",  # Missing employment history
            assets=80000.0,
            liabilities=35000.0
        ),
        "emily": BorrowerInfo(
            name="Emily Davis",
            credit_score=720,
            annual_income=78000.0,
            debt_to_income_ratio=0.30,
            employment_history="Nurse at City Hospital for 4 years",
            assets=120000.0,
            liabilities=0.0  # Missing liability information
        ),
        "robert": BorrowerInfo(
            name="Robert Wilson",
            credit_score=0,  # Missing credit score
            annual_income=0.0,  # Missing income
            debt_to_income_ratio=0.0,  # Missing DTI
            employment_history="",  # Missing employment
            assets=0.0,  # Missing assets
            liabilities=0.0  # Missing liabilities - very incomplete file
        ),
    }
    
    # Use first name from request_id to select borrower (simplified logic)
    borrower_key = "john"  # default
    if "sarah" in request_id.lower():
        borrower_key = "sarah"
    elif "michael" in request_id.lower():
        borrower_key = "michael"
    elif "emily" in request_id.lower():
        borrower_key = "emily"
    elif "robert" in request_id.lower():
        borrower_key = "robert"
    
    borrower = borrowers.get(borrower_key, borrowers["john"])
    
    # Generate mock collateral info with some missing data
    if borrower_key in ["sarah", "robert"]:
        # Missing collateral information
        collateral = CollateralInfo(
            property_type="Property Type Not Provided" if borrower_key == "robert" else "Single Family Residence",
            property_value=0.0 if borrower_key == "robert" else max(borrower.annual_income * 3.5, 200000),
            ltv_ratio=0.0 if borrower_key == "robert" else 0.75,
            appraisal_date="" if borrower_key == "robert" else "Pending Appraisal",
            address="Address Not Provided" if borrower_key == "robert" else f"Property Address Pending, {['Denver', 'Austin', 'Seattle'][random.randint(0, 2)]}"
        )
    else:
        collateral = CollateralInfo(
            property_type="Single Family Residence",
            property_value=max(borrower.annual_income * 3.5, 250000) if borrower.annual_income > 0 else 300000,
            ltv_ratio=0.75,
            appraisal_date="2024-01-15",
            address=f"123 Main St, {['Denver', 'Austin', 'Seattle'][random.randint(0, 2)]}, CO 80202"
        )
    
    # Calculate loan amount based on collateral
    loan_amount = collateral.property_value * collateral.ltv_ratio if collateral.property_value > 0 else 250000
    
    # Generate pricing info with missing data for some borrowers
    if borrower_key == "robert":
        # Very incomplete pricing data
        pricing = PricingInfo(
            interest_rate=0.0,  # Rate pending
            loan_term_months=0,  # Term not determined
            monthly_payment=0.0,  # Payment pending
            origination_fee=0.0,  # Fees pending
            processing_fee=0.0,
            total_fees=0.0
        )
    elif borrower_key in ["sarah", "michael"]:
        # Partially missing pricing
        pricing = PricingInfo(
            interest_rate=0.0 if borrower.credit_score == 0 else 6.5 + (750 - borrower.credit_score) * 0.01,
            loan_term_months=360,
            monthly_payment=0.0,  # Payment calculation pending
            origination_fee=loan_amount * 0.01 if loan_amount > 0 else 0.0,
            processing_fee=1500.0,
            total_fees=0.0  # Total pending calculation
        )
    else:
        # Complete pricing data
        pricing = PricingInfo(
            interest_rate=6.5 + (750 - borrower.credit_score) * 0.01,
            loan_term_months=360,
            monthly_payment=loan_amount * 0.006,
            origination_fee=loan_amount * 0.01,
            processing_fee=1500.0,
            total_fees=loan_amount * 0.01 + 1500.0
        )
    
    # Generate detailed request
    detailed_request = DetailedCreditRequest(
        request_id=request_id,
        borrower=borrower,
        collateral=collateral,
        pricing=pricing,
        loan_amount=loan_amount,
        loan_purpose="Home Purchase" if borrower_key != "robert" else "Purpose Not Specified",
        status="pending",
        risk_rating="Pending Assessment" if borrower_key == "robert" else ("Medium" if borrower.credit_score > 700 else "Medium-High"),
        conditions=get_conditions_for_borrower(borrower_key),
        covenants=get_covenants_for_borrower(borrower_key),
        guarantors=get_guarantors_for_borrower(borrower_key),
        regulatory_notes=get_regulatory_notes_for_borrower(borrower_key),
        created_date="2024-01-10",
        updated_date="2024-01-15"
    )
    
    return detailed_request

# Function to fetch credit request details (for Agent use)
async def fetch_credit_request_details(request_id: str) -> str:
    """
    Fetch detailed credit request information from the external API.
    This function is called by the Agent when it needs credit request details.
    """
    try:
        # In a real implementation, this would call an external API
        # For now, we'll call our own mock API endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/credit-requests/{request_id}")
            if response.status_code == 200:
                data = response.json()
                
                # Format the data for the Agent
                formatted_data = f"""
CREDIT REQUEST DETAILS FOR {request_id}:

BORROWER INFORMATION:
- Name: {data['borrower']['name']}
- Credit Score: {data['borrower']['credit_score']}
- Annual Income: ${data['borrower']['annual_income']:,.2f}
- Debt-to-Income Ratio: {data['borrower']['debt_to_income_ratio']:.1%}
- Employment: {data['borrower']['employment_history']}
- Assets: ${data['borrower']['assets']:,.2f}
- Liabilities: ${data['borrower']['liabilities']:,.2f}

COLLATERAL INFORMATION:
- Property Type: {data['collateral']['property_type']}
- Property Value: ${data['collateral']['property_value']:,.2f}
- LTV Ratio: {data['collateral']['ltv_ratio']:.1%}
- Appraisal Date: {data['collateral']['appraisal_date']}
- Address: {data['collateral']['address']}

PRICING & FEES:
- Interest Rate: {data['pricing']['interest_rate']:.2%}
- Loan Term: {data['pricing']['loan_term_months']} months
- Monthly Payment: ${data['pricing']['monthly_payment']:,.2f}
- Origination Fee: ${data['pricing']['origination_fee']:,.2f}
- Processing Fee: ${data['pricing']['processing_fee']:,.2f}
- Total Fees: ${data['pricing']['total_fees']:,.2f}

LOAN DETAILS:
- Loan Amount: ${data['loan_amount']:,.2f}
- Loan Purpose: {data['loan_purpose']}
- Status: {data['status']}
- Risk Rating: {data['risk_rating']}

CONDITIONS:
{chr(10).join(f"- {condition}" for condition in data['conditions'])}

COVENANTS:
{chr(10).join(f"- {covenant}" for covenant in data['covenants'])}

REGULATORY NOTES:
{data['regulatory_notes']}

DATES:
- Created: {data['created_date']}
- Updated: {data['updated_date']}
"""
                return formatted_data
            else:
                return f"Error fetching credit request details: API returned status {response.status_code}"
    except Exception as e:
        return f"Error fetching credit request details: {str(e)}"

@app.post("/chat")
async def chat_with_agent(chat_message: ChatMessage):
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
    if request_id_match:
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

@app.post("/generate-summary")
async def generate_summary(chat_message: ChatMessage):
    # Use the provided message text for summary generation
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

@app.post("/generate-credit-memo")
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

Instructions for the team:
1. Credit Data Specialist: Thoroughly analyze and organize all the credit request data above. Focus on key financial metrics, risk factors, and data completeness.

2. Credit Memo Specialist: Create a comprehensive HTML credit memo with these exact sections:

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

def main():
    print("Starting Agentic Lender Memo API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()