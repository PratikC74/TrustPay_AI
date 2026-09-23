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


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="TrustPay AI",
    description="AI-powered programmable payment platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
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