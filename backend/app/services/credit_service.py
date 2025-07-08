from typing import List
import httpx
from ..models import BorrowerInfo, CollateralInfo, PricingInfo, DetailedCreditRequest
import random

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

def get_sample_borrowers():
    """Get sample borrower data with missing information for testing"""
    return {
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