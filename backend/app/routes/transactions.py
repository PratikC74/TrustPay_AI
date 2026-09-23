from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.risk_assessment import RiskAssessment
from app.models.audit_log import AuditLog
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionStatusUpdate,
)
from app.services.ai_service import analyze_transaction


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


# ==================================================
# CREATE TRANSACTION
# ==================================================
@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    # Check user exists
    user = (
        db.query(User)
        .filter(User.id == transaction_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Check duplicate reference
    existing_transaction = (
        db.query(Transaction)
        .filter(
            Transaction.transaction_reference
            == transaction_data.transaction_reference
        )
        .first()
    )

    if existing_transaction:
        raise HTTPException(
            status_code=409,
            detail="Transaction reference already exists",
        )

    # Create transaction
    transaction = Transaction(
        user_id=transaction_data.user_id,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        payment_method=transaction_data.payment_method,
        status=transaction_data.status,
        transaction_reference=transaction_data.transaction_reference,
    )

    db.add(transaction)
    db.flush()

    try:
        # AI risk analysis
        ai_result = analyze_transaction(
            amount=float(transaction.amount),
            currency=transaction.currency,
            payment_method=transaction.payment_method,
            status=transaction.status,
            transaction_reference=transaction.transaction_reference,
        )

        # Create risk assessment
        risk_assessment = RiskAssessment(
            transaction_id=transaction.id,
            risk_score=ai_result["risk_score"],
            risk_level=ai_result["risk_level"],
            is_suspicious=ai_result["is_suspicious"],
            reason=ai_result["reason"],
            ai_recommendation=ai_result["ai_recommendation"],
        )

        db.add(risk_assessment)

        # Audit transaction creation
        audit_log = AuditLog(
            user_id=int(current_user["sub"]),
            transaction_id=transaction.id,
            action="CREATE",
            old_status=None,
            new_status=transaction.status,
        )

        db.add(audit_log)

        db.commit()

        db.refresh(transaction)
        db.refresh(risk_assessment)

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Transaction processing failed: {str(e)}",
        )

    return {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "payment_method": transaction.payment_method,
        "status": transaction.status,
        "transaction_reference": transaction.transaction_reference,
        "risk_assessment": risk_assessment,
    }


# ==================================================
# GET TRANSACTIONS
# Supports:
# ?status=review
# ?risk_level=medium
# ?search=TPA
# ==================================================
@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    query = db.query(Transaction)

    # Filter by status
    if status:
        query = query.filter(
            Transaction.status == status.lower()
        )

    transactions = query.all()

    result = []

    for transaction in transactions:
        risk_assessment = (
            db.query(RiskAssessment)
            .filter(
                RiskAssessment.transaction_id
                == transaction.id
            )
            .first()
        )

        # Filter by risk level
        if risk_level:
            if not risk_assessment:
                continue

            if (
                risk_assessment.risk_level.lower()
                != risk_level.lower()
            ):
                continue

        # Search
        if search:
            search_text = search.lower().strip()

            reference = (
                transaction.transaction_reference or ""
            ).lower()

            payment_method = (
                transaction.payment_method or ""
            ).lower()

            if (
                search_text not in reference
                and search_text not in payment_method
            ):
                continue

        result.append(
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "payment_method": transaction.payment_method,
                "status": transaction.status,
                "transaction_reference": transaction.transaction_reference,
                "risk_assessment": risk_assessment,
            }
        )

    return result


# ==================================================
# GET PAYMENT DECISION
# ==================================================
@router.post("/{transaction_id}/decision")
def get_payment_decision(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    risk_assessment = (
        db.query(RiskAssessment)
        .filter(
            RiskAssessment.transaction_id
            == transaction_id
        )
        .first()
    )

    if not risk_assessment:
        raise HTTPException(
            status_code=404,
            detail="Risk assessment not found",
        )

    risk_level = risk_assessment.risk_level.lower()

    if risk_level == "low":
        decision = "APPROVED"
    elif risk_level == "medium":
        decision = "REVIEW"
    else:
        decision = "BLOCKED"

    return {
        "transaction_id": transaction_id,
        "risk_score": risk_assessment.risk_score,
        "risk_level": risk_assessment.risk_level,
        "decision": decision,
        "reason": risk_assessment.reason,
        "recommendation": risk_assessment.ai_recommendation,
    }


# ==================================================
# UPDATE TRANSACTION STATUS
# ==================================================
@router.patch("/{transaction_id}/status")
def update_transaction_status(
    transaction_id: int,
    status_data: TransactionStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    allowed_statuses = {
        "approved",
        "review",
        "blocked",
    }

    status = status_data.status.lower()

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Status must be approved, review, or blocked"
            ),
        )

    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    # Completed transactions cannot be changed
    if transaction.status == "completed":
        raise HTTPException(
            status_code=403,
            detail="Completed transactions cannot be modified.",
        )

    risk_assessment = (
        db.query(RiskAssessment)
        .filter(
            RiskAssessment.transaction_id
            == transaction_id
        )
        .first()
    )

    if risk_assessment:
        risk_level = risk_assessment.risk_level.lower()

        # LOW -> APPROVED
        if status == "approved" and risk_level != "low":
            recommended_action = (
                "REVIEW"
                if risk_level == "medium"
                else "BLOCK"
            )

            raise HTTPException(
                status_code=403,
                detail=(
                    f"{risk_level.upper()}-risk transaction "
                    f"cannot be approved. "
                    f"Recommended action: "
                    f"{recommended_action}."
                ),
            )

        # HIGH -> BLOCKED
        if status == "review" and risk_level == "high":
            raise HTTPException(
                status_code=403,
                detail=(
                    "High-risk transactions "
                    "should be blocked."
                ),
            )

        # LOW should not be blocked
        if status == "blocked" and risk_level == "low":
            raise HTTPException(
                status_code=403,
                detail=(
                    "Low-risk transactions are "
                    "recommended for approval."
                ),
            )

    # Save old status for audit
    old_status = transaction.status

    # Update status
    transaction.status = status

    # Create audit log
    audit_log = AuditLog(
        user_id=int(current_user["sub"]),
        transaction_id=transaction.id,
        action=status.upper(),
        old_status=old_status,
        new_status=status,
    )

    db.add(audit_log)

    db.commit()
    db.refresh(transaction)

    return {
        "message": "Transaction status updated",
        "transaction_id": transaction.id,
        "status": transaction.status,
    }


# ==================================================
# EXECUTE PAYMENT
# ==================================================
@router.post("/{transaction_id}/execute")
def execute_payment(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    risk_assessment = (
        db.query(RiskAssessment)
        .filter(
            RiskAssessment.transaction_id
            == transaction_id
        )
        .first()
    )

    if not risk_assessment:
        raise HTTPException(
            status_code=404,
            detail="Risk assessment not found",
        )

    # Already completed
    if transaction.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Transaction is already completed.",
        )

    risk_level = risk_assessment.risk_level.lower()

    # HIGH risk
    if risk_level == "high":
        raise HTTPException(
            status_code=403,
            detail=(
                "Payment blocked because the "
                "transaction is high risk."
            ),
        )

    # MEDIUM risk
    if risk_level == "medium":
        raise HTTPException(
            status_code=403,
            detail=(
                "Payment requires manual review "
                "before execution."
            ),
        )

    # Only approved transactions can execute
    if transaction.status != "approved":
        raise HTTPException(
            status_code=403,
            detail=(
                "Transaction must be approved "
                "before payment execution."
            ),
        )

    # Save old status
    old_status = transaction.status

    # Complete payment
    transaction.status = "completed"

    # Create audit log
    audit_log = AuditLog(
        user_id=int(current_user["sub"]),
        transaction_id=transaction.id,
        action="EXECUTE",
        old_status=old_status,
        new_status="completed",
    )

    db.add(audit_log)

    db.commit()
    db.refresh(transaction)

    return {
        "message": "Payment executed successfully",
        "transaction_id": transaction.id,
        "transaction_reference": transaction.transaction_reference,
        "amount": transaction.amount,
        "status": transaction.status,
        "risk_level": risk_level,
        "payment_result": "SUCCESS",
    }