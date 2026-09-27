import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.transaction import Transaction
from app.models.risk_assessment import RiskAssessment
from app.models.audit_log import AuditLog

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_full_suite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    hashed_pwd = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
    admin_user = User(
        id=1,
        name="Pratik Admin",
        email="pratik@example.com",
        phone="1234567890",
        role="admin",
        password_hash=hashed_pwd,
    )
    db.add(admin_user)

    hashed_user_pwd = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode("utf-8")
    regular_user = User(
        id=2,
        name="Standard User",
        email="user@example.com",
        phone="0987654321",
        role="user",
        password_hash=hashed_user_pwd,
    )
    db.add(regular_user)

    db.commit()
    db.close()
    yield


client = TestClient(app)


def get_admin_token():
    resp = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    return resp.json()["access_token"]


def get_user_token():
    resp = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "user123"},
    )
    return resp.json()["access_token"]


# 1. System Health & Infrastructure
def test_system_endpoints():
    r1 = client.get("/")
    assert r1.status_code == 200
    assert "message" in r1.json()

    r2 = client.get("/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "healthy"

    r3 = client.get("/db-test")
    assert r3.status_code == 200
    assert r3.json()["database"] == "connected"


# 2. Authentication Endpoint Audit
def test_authentication():
    # Valid login
    r1 = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    assert r1.status_code == 200
    data = r1.json()
    assert "access_token" in data
    assert data["role"] == "admin"

    # Invalid password
    r2 = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "wrongpassword"},
    )
    assert r2.status_code == 401

    # Non-existent user
    r3 = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password"},
    )
    assert r3.status_code == 401


# 3. User Management Endpoint Audit
def test_user_management():
    # Create user
    r1 = client.post(
        "/users/",
        json={
            "name": "New User",
            "email": "newuser@example.com",
            "phone": "5551234567",
            "role": "user",
            "password": "newpassword123",
        },
    )
    assert r1.status_code == 200
    assert r1.json()["email"] == "newuser@example.com"

    # Get users
    r2 = client.get("/users/")
    assert r2.status_code == 200
    users = r2.json()
    assert len(users) >= 3


# 4. Transaction Creation & Risk Analysis Audit
def test_transaction_creation_and_risk():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Low risk creation
    r_low = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 250,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "REF-LOW-RISK-01",
        },
        headers=headers,
    )
    assert r_low.status_code == 200
    assert r_low.json()["risk_assessment"]["risk_level"] == "low"

    # Medium risk creation
    r_med = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 60000,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "REF-MED-RISK-01",
        },
        headers=headers,
    )
    assert r_med.status_code == 200
    assert r_med.json()["risk_assessment"]["risk_level"] == "medium"

    # High risk creation (amount >= 1,000,000)
    r_high = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 1500000,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "REF-HIGH-RISK-01",
        },
        headers=headers,
    )
    assert r_high.status_code == 200
    assert r_high.json()["risk_assessment"]["risk_level"] == "high"

    # Duplicate transaction reference error (409)
    r_dup = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "REF-LOW-RISK-01",
        },
        headers=headers,
    )
    assert r_dup.status_code == 409

    # Non-existent user error (404)
    r_nouser = client.post(
        "/transactions/",
        json={
            "user_id": 9999,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "REF-NOUSER-01",
        },
        headers=headers,
    )
    assert r_nouser.status_code == 404

    # Unauthenticated request (401)
    r_unauth = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "REF-UNAUTH-01",
        },
    )
    assert r_unauth.status_code == 401


# 5. Transaction Retrieval & Filter Audit
def test_transaction_queries():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy data
    client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "QUERY-REF-01",
        },
        headers=headers,
    )

    # Get all
    r1 = client.get("/transactions/", headers=headers)
    assert r1.status_code == 200
    assert len(r1.json()) >= 1

    # Filter by status
    r2 = client.get("/transactions/?status=pending", headers=headers)
    assert r2.status_code == 200

    # Filter by risk level
    r3 = client.get("/transactions/?risk_level=low", headers=headers)
    assert r3.status_code == 200

    # Search filter
    r4 = client.get("/transactions/?search=QUERY-REF", headers=headers)
    assert r4.status_code == 200
    assert len(r4.json()) == 1


# 6. Payment Decision & Status Workflow Audit
def test_transaction_workflow():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create low-risk transaction
    res = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "WORKFLOW-LOW-01",
        },
        headers=headers,
    )
    tx_id = res.json()["id"]

    # Decision endpoint
    dec = client.post(f"/transactions/{tx_id}/decision")
    assert dec.status_code == 200
    assert dec.json()["decision"] == "APPROVED"

    # Update status to approved
    st_app = client.patch(
        f"/transactions/{tx_id}/status",
        json={"status": "approved"},
        headers=headers,
    )
    assert st_app.status_code == 200

    # Execute payment
    exe = client.post(
        f"/transactions/{tx_id}/execute",
        headers=headers,
    )
    assert exe.status_code == 200
    assert exe.json()["status"] == "completed"

    # Attempt to modify completed transaction (403)
    mod_comp = client.patch(
        f"/transactions/{tx_id}/status",
        json={"status": "review"},
        headers=headers,
    )
    assert mod_comp.status_code == 403

    # High risk blocking test
    res_high = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 2000000,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "WORKFLOW-HIGH-01",
        },
        headers=headers,
    )
    high_tx_id = res_high.json()["id"]

    # Block high risk
    st_block = client.patch(
        f"/transactions/{high_tx_id}/status",
        json={"status": "blocked"},
        headers=headers,
    )
    assert st_block.status_code == 200

    # Attempt to execute high risk payment (403)
    exe_high = client.post(
        f"/transactions/{high_tx_id}/execute",
        headers=headers,
    )
    assert exe_high.status_code == 403


# 7. Audit Log Access Control
def test_audit_logs_security():
    admin_token = get_admin_token()
    user_token = get_user_token()

    # Admin access
    r_admin = client.get(
        "/audit-logs/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_admin.status_code == 200

    # Non-admin user access (403 Forbidden)
    r_user = client.get(
        "/audit-logs/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r_user.status_code == 403

    # Unauthenticated access (401 Unauthorized)
    r_unauth = client.get("/audit-logs/")
    assert r_unauth.status_code == 401


# 8. Risk Assessment Standalone Endpoints
def test_risk_assessment_endpoints():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    tx_res = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 500,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "RISK-TEST-01",
        },
        headers=headers,
    )
    tx_id = tx_res.json()["id"]

    # List risk assessments
    r_list = client.get("/risk-assessments/")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    # Analyze risk endpoint
    r_an = client.post(f"/risk-assessments/analyze/{tx_id}")
    assert r_an.status_code == 200
    assert "risk_score" in r_an.json()
