import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"

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

    # Seed admin user for tests
    db = TestingSessionLocal()
    hashed_pwd = bcrypt.hashpw(
        b"admin123", bcrypt.gensalt()
    ).decode("utf-8")
    admin_user = User(
        id=1,
        name="Pratik Admin",
        email="pratik@example.com",
        phone="1234567890",
        role="admin",
        password_hash=hashed_pwd,
    )
    db.add(admin_user)
    db.commit()
    db.close()
    yield


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login():
    response = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["role"] == "admin"


def test_transactions_requires_auth():
    response = client.get("/transactions/")
    assert response.status_code == 401


def test_authenticated_transactions():
    login_resp = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/transactions/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_transaction():
    login_resp = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]
    reference = "PYTEST-REF-1001"

    response = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 1000,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": reference,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_reference"] == reference
    assert "risk_assessment" in data


def test_audit_logs():
    login_resp = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/audit-logs/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_transaction_status():
    login_resp = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]

    # First create a transaction
    create_resp = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "UPDATE-STATUS-REF-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 200
    tx_id = create_resp.json()["id"]

    response = client.patch(
        f"/transactions/{tx_id}/status",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (200, 403)


def test_approve_and_execute_low_risk():
    login_resp = client.post(
        "/auth/login",
        json={"email": "pratik@example.com", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]

    create_resp = client.post(
        "/transactions/",
        json={
            "user_id": 1,
            "amount": 100,
            "currency": "INR",
            "payment_method": "UPI",
            "status": "pending",
            "transaction_reference": "EXECUTE-LOW-RISK-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert create_resp.status_code == 200
    tx_data = create_resp.json()
    tx_id = tx_data["id"]
    assert tx_data["risk_assessment"]["risk_level"].lower() == "low"

    approve_resp = client.patch(
        f"/transactions/{tx_id}/status",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_resp.status_code == 200

    execute_resp = client.post(
        f"/transactions/{tx_id}/execute",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert execute_resp.status_code == 200
    data = execute_resp.json()
    assert data["status"] == "completed"