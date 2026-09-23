import json
import urllib.request
import time

BASE_URL = "http://127.0.0.1:8000"


def test_health():
    with urllib.request.urlopen(f"{BASE_URL}/health") as response:
        assert response.status == 200


def test_login():
    payload = json.dumps({
        "email": "pratik@example.com",
        "password": "admin123",
    }).encode()

    request = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        body = json.loads(response.read().decode())

        assert response.status == 200
        assert "access_token" in body
        assert body["role"] == "admin"


def test_transactions_requires_auth():
    request = urllib.request.Request(
        f"{BASE_URL}/transactions/",
        method="GET",
    )

    try:
        urllib.request.urlopen(request)
        assert False, "Expected 401 Unauthorized"
    except urllib.error.HTTPError as error:
        assert error.code == 401



def test_authenticated_transactions():
    login_payload = json.dumps({
        "email": "pratik@example.com",
        "password": "admin123",
    }).encode()

    login_request = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(login_request) as response:
        login_data = json.loads(response.read().decode())

    token = login_data["access_token"]

    request = urllib.request.Request(
        f"{BASE_URL}/transactions/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )

    with urllib.request.urlopen(request) as response:
        assert response.status == 200


def test_create_transaction():
    login_payload = json.dumps({
        "email": "pratik@example.com",
        "password": "admin123",
    }).encode()

    login_request = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(login_request) as response:
        login_data = json.loads(response.read().decode())

    token = login_data["access_token"]
    reference = f"PYTEST-{int(time.time() * 1000)}"
    transaction_payload = json.dumps({
        "user_id": 1,
        "amount": 1000,
        "currency": "INR",
        "payment_method": "UPI",
        "status": "pending",
        "transaction_reference": reference,
    }).encode()

    request = urllib.request.Request(
        f"{BASE_URL}/transactions/",
        data=transaction_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode())

        assert response.status == 200
        assert data["transaction_reference"] == reference
        assert "risk_assessment" in data


def test_audit_logs():
    login_payload = json.dumps({
        "email": "pratik@example.com",
        "password": "admin123",
    }).encode()

    login_request = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(login_request) as response:
        login_data = json.loads(response.read().decode())

    token = login_data["access_token"]

    request = urllib.request.Request(
        f"{BASE_URL}/audit-logs/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode())

        assert response.status == 200
        assert isinstance(data, list)



def test_update_transaction_status():
    login_payload = json.dumps({
        "email": "pratik@example.com",
        "password": "admin123",
    }).encode()

    login_request = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(login_request) as response:
        token = json.loads(response.read().decode())["access_token"]

    transaction_id = 14

    payload = json.dumps({
        "status": "approved"
    }).encode()

    request = urllib.request.Request(
        f"{BASE_URL}/transactions/{transaction_id}/status",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="PATCH",
    )

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())
            assert response.status == 200
            assert data["status"] == "approved"
    except urllib.error.HTTPError as error:
        assert error.code in (200, 403)




def test_approve_and_execute_low_risk():
    login_payload = json.dumps({
        "email": "pratik@example.com",
        "password": "admin123",
    }).encode()

    login_request = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(login_request) as response:
        token = json.loads(
            response.read().decode()
        )["access_token"]

    reference = f"EXEC-{int(time.time() * 1000)}"

    payload = json.dumps({
        "user_id": 1,
        "amount": 100,
        "currency": "INR",
        "payment_method": "UPI",
        "status": "pending",
        "transaction_reference": reference,
    }).encode()

    create_request = urllib.request.Request(
        f"{BASE_URL}/transactions/",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with urllib.request.urlopen(create_request) as response:
        transaction = json.loads(
            response.read().decode()
        )

    transaction_id = transaction["id"]

    assert transaction["risk_assessment"]["risk_level"].lower() == "low"

    approve_payload = json.dumps({
        "status": "approved"
    }).encode()

    approve_request = urllib.request.Request(
        f"{BASE_URL}/transactions/{transaction_id}/status",
        data=approve_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="PATCH",
    )

    with urllib.request.urlopen(approve_request) as response:
        assert response.status == 200

    execute_request = urllib.request.Request(
        f"{BASE_URL}/transactions/{transaction_id}/execute",
        headers={
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    with urllib.request.urlopen(execute_request) as response:
        data = json.loads(
            response.read().decode()
        )

        assert response.status == 200
        assert data["status"] == "completed"