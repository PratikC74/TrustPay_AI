# TrustPay AI

AI-Powered Payment Risk & Decision Platform

## Features

- **JWT Authentication**: User login and role-based access control (Admin & User).
- **Payment Risk Assessment**: AI-based transaction analysis using OpenAI (`gpt-4o-mini`) with automatic fallback to a local rule engine.
- **Decision Engine**: Low / Medium / High risk classification leading to Approved / Review / Block decisions.
- **Programmable Payment Execution**: Automated payment settlement for low-risk approved transactions.
- **Audit Logging**: Real-time tracking of transaction status changes and payment execution.
- **Interactive Dashboard**: Modern React + Vite frontend with risk summary filters, search, and metrics.
- **Automated Testing**: Complete integration test suite using FastAPI `TestClient` and `pytest`.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL, PyJWT, OpenAI API, Pytest
- **Frontend**: React 19, Vite 8, JavaScript
- **Database / Infra**: PostgreSQL, Docker

## Project Structure

```text
TrustPayAI/
├── backend/          # FastAPI backend service
│   ├── app/          # App models, routes, schemas, and AI services
│   └── tests/        # Pytest API integration tests
├── frontend/         # React + Vite frontend dashboard
├── docker-compose.yml # PostgreSQL database container setup
└── README.md
```

## Local Setup

### 1. Database
```bash
docker compose up -d
```

### 2. Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Production Deployment Guide

### Option 1: Deploy on Render (Recommended for Fast Cloud Setup)
1. **Database**: Create a **PostgreSQL Database** instance on Render.
2. **Backend**:
   - Create a **Web Service** pointing to `backend/`.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     - `DATABASE_URL`: `postgresql+psycopg://<user>:<password>@<host>/<database>`
     - `JWT_SECRET`: `<your-random-secret-key>`
     - `OPENAI_API_KEY`: `<your-openai-api-key>`
3. **Frontend**:
   - Create a **Static Site** on Render or Vercel pointing to `frontend/`.
   - Build Command: `npm run build`
   - Publish Directory: `dist`
   - Rewrite rule / Proxy: Route `/api/*` to your backend service URL.

### Option 2: Deploy using Docker / Render / Railway
You can also package the backend and frontend into Docker containers or deploy to platforms like Render, Railway, Fly.io, or AWS.
