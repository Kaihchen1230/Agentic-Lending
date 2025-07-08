from typing import List
import random
from ..models import CreditRequest, BorrowerInfo, CollateralInfo, PricingInfo, DetailedCreditRequest
from .credit_service import (
    get_sample_borrowers, 
    get_conditions_for_borrower,
    get_covenants_for_borrower, 
    get_guarantors_for_borrower,
    get_regulatory_notes_for_borrower
)

def get_mock_credit_requests() -> List[CreditRequest]:
    """Generate mock credit request list"""
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

def get_mock_detailed_credit_request(request_id: str) -> DetailedCreditRequest:
    """Generate mock detailed credit request"""
    borrowers = get_sample_borrowers()
    
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