import json
from openai import OpenAI
from app.config import settings


client = OpenAI(api_key=settings.openai_api_key)


def fallback_risk_analysis(
    amount: float,
    currency: str,
    payment_method: str,
    status: str,
    transaction_reference: str,
):
    score = 5

    # Amount-based risk
    if amount >= 1000000:
        score += 70
    elif amount >= 100000:
        score += 50
    elif amount >= 50000:
        score += 35
    elif amount >= 10000:
        score += 20
    elif amount >= 5000:
        score += 10

    # Pending transactions
    if status.lower() == "pending":
        score += 5

    # UPI
    if payment_method.lower() == "upi":
        score += 5

    # Suspicious reference keywords
    suspicious_words = [
        "fraud",
        "test-fraud",
        "suspicious",
        "unknown",
    ]

    reference_lower = transaction_reference.lower()

    if any(word in reference_lower for word in suspicious_words):
        score += 20

    score = min(score, 100)

    if score >= 70:
        risk_level = "high"
    elif score >= 35:
        risk_level = "medium"
    else:
        risk_level = "low"

    is_suspicious = score >= 60

    if risk_level == "high":
        reason = (
            "High transaction risk based on amount and "
            "transaction characteristics."
        )
        recommendation = (
            "Block the payment and perform enhanced verification."
        )
    elif risk_level == "medium":
        reason = (
            "Moderate transaction risk requires additional verification."
        )
        recommendation = (
            "Review the transaction and verify payment details."
        )
    else:
        reason = (
            "Low-risk transaction with no major suspicious indicators."
        )
        recommendation = (
            "Proceed after confirming successful payment settlement."
        )

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "is_suspicious": is_suspicious,
        "reason": reason,
        "ai_recommendation": recommendation,
    }


def analyze_transaction(
    amount: float,
    currency: str,
    payment_method: str,
    status: str,
    transaction_reference: str,
):
    prompt = f"""
You are a payment risk analysis assistant for TrustPay AI.

Analyze this transaction:

Amount: {amount}
Currency: {currency}
Payment Method: {payment_method}
Status: {status}
Transaction Reference: {transaction_reference}

Return ONLY valid JSON:

{{
    "risk_score": 0,
    "risk_level": "low",
    "is_suspicious": false,
    "reason": "reason here",
    "ai_recommendation": "recommendation here"
}}
"""

    try:
        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions=(
                "You are a financial transaction risk analysis assistant."
            ),
            input=prompt,
            text={
                "format": {
                    "type": "json_object"
                }
            },
        )

        return json.loads(response.output_text)

    except Exception as exc:
        error_text = str(exc).lower()

        # Use local risk engine when OpenAI quota is exhausted
        if (
            "insufficient_quota" in error_text
            or "credit_balance_exhausted" in error_text
            or "no credits remaining" in error_text
        ):
            return fallback_risk_analysis(
                amount,
                currency,
                payment_method,
                status,
                transaction_reference,
            )

        raise