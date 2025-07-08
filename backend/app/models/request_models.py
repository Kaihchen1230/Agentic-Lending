from pydantic import BaseModel
from typing import List, Optional

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