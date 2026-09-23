from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.risk_assessment import RiskAssessment
from app.models.transaction import Transaction
from app.schemas.risk_assessment import (
    RiskAssessmentCreate,
    RiskAssessmentResponse
)
from app.services.ai_service import analyze_transaction


router = APIRouter(
    prefix="/risk-assessments",
    tags=["Risk Assessments"]
)


@router.post("/", response_model=RiskAssessmentResponse)
def create_risk_assessment(
    risk_data: RiskAssessmentCreate,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == risk_data.transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    existing = db.query(RiskAssessment).filter(
        RiskAssessment.transaction_id == risk_data.transaction_id
    ).first()

    if existing:
        existing.risk_score = risk_data.risk_score
        existing.risk_level = risk_data.risk_level
        existing.is_suspicious = risk_data.is_suspicious
        existing.reason = risk_data.reason
        existing.ai_recommendation = risk_data.ai_recommendation

        db.commit()
        db.refresh(existing)

        return existing

    risk_assessment = RiskAssessment(
        transaction_id=risk_data.transaction_id,
        risk_score=risk_data.risk_score,
        risk_level=risk_data.risk_level,
        is_suspicious=risk_data.is_suspicious,
        reason=risk_data.reason,
        ai_recommendation=risk_data.ai_recommendation
    )

    db.add(risk_assessment)
    db.commit()
    db.refresh(risk_assessment)

    return risk_assessment


@router.get("/", response_model=list[RiskAssessmentResponse])
def get_risk_assessments(
    db: Session = Depends(get_db)
):
    return db.query(RiskAssessment).all()


@router.post("/analyze/{transaction_id}")
def analyze_transaction_risk(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    try:
        ai_result = analyze_transaction(
            amount=float(transaction.amount),
            currency=transaction.currency,
            payment_method=transaction.payment_method,
            status=transaction.status,
            transaction_reference=transaction.transaction_reference
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )

    existing = db.query(RiskAssessment).filter(
        RiskAssessment.transaction_id == transaction_id
    ).first()

    if existing:
        existing.risk_score = ai_result["risk_score"]
        existing.risk_level = ai_result["risk_level"]
        existing.is_suspicious = ai_result["is_suspicious"]
        existing.reason = ai_result["reason"]
        existing.ai_recommendation = ai_result["ai_recommendation"]

        db.commit()
        db.refresh(existing)

        return existing

    risk_assessment = RiskAssessment(
        transaction_id=transaction_id,
        risk_score=ai_result["risk_score"],
        risk_level=ai_result["risk_level"],
        is_suspicious=ai_result["is_suspicious"],
        reason=ai_result["reason"],
        ai_recommendation=ai_result["ai_recommendation"]
    )

    db.add(risk_assessment)
    db.commit()
    db.refresh(risk_assessment)

    return risk_assessment