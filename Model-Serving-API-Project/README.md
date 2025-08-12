# Crypto-Model-API

A FastAPI service that serves machine learning model predictions via REST API. Supports both **synchronous** and **asynchronous** model inference using **Celery + Redis**, secured with **Auth0 JWT authentication**.

---

## 🛠️ Setup Instructions

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```
thi
3. Run the FastAPI app locally:

```bash
cd backend
uvicorn main:app --reload
```

> ⚠️ For async jobs, Redis must be running and Celery must be started manually unless using Docker.

---

## 🐳 Running With Docker (Recommended)

From the backend directory:

```bash
docker compose up --build
```

To run in the background:

```bash
docker compose up --build -d
```

This launches:

- FastAPI app on `localhost:8080`
- Redis for background task queuing
- Celery worker to run async model inference

---

## 🚀 API Endpoints

| Method | Endpoint                   | Description                             |
| ------ | -------------------------- | --------------------------------------- |
| GET    | `/v2/health/live`          | Basic health check                      |
| GET    | `/v2/health/ready`         | Readiness check (models + Celery ready) |
| POST   | `/v2/predict`              | Submit input data for prediction        |
| GET    | `/v2/jobs/{job_id}`        | Check status of an async prediction     |
| GET    | `/v2/jobs/{job_id}/result` | Retrieve final result of async job      |
| GET    | `/v2/models`               | List available models                   |
| GET    | `/v2/models/{model_id}`    | Retrieve metadata for a specific model  |

Supports:

- `dummy-logistic-model`: sync
- `dummy-slow-model`: async

---

## 🧪 Local Testing (with HTML UI)

A basic frontend is included at `/static/index.html` for quickly testing:

- Submitting sync/async jobs
- Tracking job status
- Fetching job results

---

## ⚙️ Architecture

- **FastAPI** – REST API server
- **Auth0** – Authentication & JWT validation
- **Celery** – Background task queue for async inference
- **Redis** – Broker & result backend for Celery
- **Pandas / Scikit-learn** – Dummy models

---

## ✅ Features Implemented

- ✅ Sync + async prediction routes
- ✅ Job queuing with Celery
- ✅ Redis integration
- ✅ Auth0 JWT authentication with JWKS caching
- ✅ Docker + Docker Compose setup
- ✅ Custom HTML client for testing
- ✅ /status + /result endpoints
- ✅ /health/live and /health/ready checks
---

## 🔒 Future Work

-Deploy to Google Cloud Run
- Move secrets to GCP Secret Manager
- Add rate limiting
- Swap in real trained ML models
- Add structured logging and error monitoring
- Restrict CORS in production
- Disable /static in production

---


