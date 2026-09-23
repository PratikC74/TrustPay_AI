from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .all()
    )

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "transaction_id": log.transaction_id,
            "action": log.action,
            "old_status": log.old_status,
            "new_status": log.new_status,
            "created_at": log.created_at,
        }
        for log in logs
    ]