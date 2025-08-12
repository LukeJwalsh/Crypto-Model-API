# Crypt0Nest-Crypto-Model-API

A FastAPI service that serves machine learning model predictions via REST API. Supports both **synchronous** and **asynchronous** model inference using **Celery + Redis**.

Built as part of the backend track at Crypt0Nest.

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

| Method | Endpoint              | Description                         |
| ------ | --------------------- | ----------------------------------- |
| GET    | `/health`             | Basic health check                  |
| GET    | `/`                   | Serves a simple HTML test client    |
| POST   | `/v1/predict`         | Submit input data for prediction    |
| GET    | `/v1/status/{job_id}` | Check status of an async prediction |
| GET    | `/v1/result/{job_id}` | Retrieve final result of async job  |

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
- **Celery** – Background task queue for async inference
- **Redis** – Broker & result backend for Celery
- **Pandas / Scikit-learn** – Dummy models

---

## ✅ Features Implemented

- ✅ Sync + async prediction routes
- ✅ Job queuing with Celery
- ✅ Redis integration
- ✅ Docker + Docker Compose setup
- ✅ Custom HTML client for testing
- ✅ `/status` + `/result` endpoints

---

## 🔒 Future Work

- Deploy to Google Cloud Run
- Add API key auth / rate limiting
- Swap in real trained ML models
- Add logging and error monitoring

---

> Built by Backend Team at Crypt0Nest 
