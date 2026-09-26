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
    # If API key is not configured, directly return fallback analysis
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-proj-placeholder"):
        return fallback_risk_analysis(
            amount,
            currency,
            payment_method,
            status,
            transaction_reference,
        )

    prompt = f"""
Analyze this transaction for risk:

Amount: {amount}
Currency: {currency}
Payment Method: {payment_method}
Status: {status}
Transaction Reference: {transaction_reference}

Return ONLY valid JSON matching this structure:
{{
    "risk_score": 15,
    "risk_level": "low",
    "is_suspicious": false,
    "reason": "Reason for risk assessment",
    "ai_recommendation": "Recommended action"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial transaction risk analysis assistant for TrustPay AI. Respond strictly in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content:
            return json.loads(content)
        raise ValueError("Empty response from AI model")

    except Exception:
        # Graceful fallback to rule-based engine on any AI error (quota, invalid key, network issue, model unavailable)
        return fallback_risk_analysis(
            amount,
            currency,
            payment_method,
            status,
            transaction_reference,
        )