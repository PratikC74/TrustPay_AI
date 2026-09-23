from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=False,
        unique=True,
        index=True
    )

    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    is_suspicious: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    ai_recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )