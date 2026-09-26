from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, engine

from app.models.user import User
from app.models.transaction import Transaction
from app.models.risk_assessment import RiskAssessment

from app.routes.users import router as users_router
from app.routes.transactions import router as transactions_router
from app.routes.auth import router as auth_router

from app.routes.risk_assessments import router as risk_assessments_router
from app.models.audit_log import AuditLog
from app.routes.audit_logs import router as audit_logs_router


import bcrypt
from app.database import SessionLocal, Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)


def seed_initial_data():
    db = SessionLocal()
    try:
        admin_user = (
            db.query(User)
            .filter(User.email == "pratik@example.com")
            .first()
        )
        if not admin_user:
            hashed_pwd = bcrypt.hashpw(
                b"admin123", bcrypt.gensalt()
            ).decode("utf-8")
            admin_user = User(
                name="Pratik Admin",
                email="pratik@example.com",
                phone="1234567890",
                role="admin",
                password_hash=hashed_pwd,
            )
            db.add(admin_user)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding initial data: {e}")
    finally:
        db.close()


seed_initial_data()


app = FastAPI(
    title="TrustPay AI",
    description="AI-powered programmable payment platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://trust-pay-ai-zeta.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(users_router)
app.include_router(transactions_router)
app.include_router(risk_assessments_router)
app.include_router(auth_router)
app.include_router(audit_logs_router)


@app.get("/")
def root():
    return {
        "message": "TrustPay AI API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TrustPay AI"
    }


@app.get("/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "result": result.scalar()
        }