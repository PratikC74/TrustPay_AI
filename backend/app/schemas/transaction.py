from decimal import Decimal

from pydantic import BaseModel


class RiskResult(BaseModel):
    id: int
    transaction_id: int
    risk_score: Decimal
    risk_level: str
    is_suspicious: bool
    reason: str | None = None
    ai_recommendation: str | None = None

    model_config = {
        "from_attributes": True
    }


class TransactionCreate(BaseModel):
    user_id: int
    amount: Decimal
    currency: str = "INR"
    payment_method: str
    status: str = "pending"
    transaction_reference: str


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    currency: str
    payment_method: str
    status: str
    transaction_reference: str
    risk_assessment: RiskResult | None = None

    model_config = {
        "from_attributes": True
    }

class TransactionStatusUpdate(BaseModel):
    status: str
