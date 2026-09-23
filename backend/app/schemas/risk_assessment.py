from decimal import Decimal

from pydantic import BaseModel


class RiskAssessmentCreate(BaseModel):
    transaction_id: int
    risk_score: Decimal
    risk_level: str
    is_suspicious: bool = False
    reason: str | None = None
    ai_recommendation: str | None = None


class RiskAssessmentResponse(BaseModel):
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






