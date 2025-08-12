import asyncio
import os
import joblib
from shared import logger
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic_settings import BaseSettings
from models import MODELS
from concurrent.futures import ThreadPoolExecutor
from routes import health, predict, jobs, models
from shared.state import MODEL_REGISTRY
from shared.load_models import load_models
from settings import settings

# ==================
# CONFIGURATION
# ==================

class Settings(BaseSettings):
    model_dir: str = "models"

settings = Settings()
API_VERSION = "/v2"

# ==================
# APP INIT
# ==================

app = FastAPI()

# ==================
# CORS
# ==================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================
# STATIC FRONTEND
# ==================

app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================
# LIFESPAN EVENTS
# ==================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Thread pool setup
    num_cores = os.cpu_count() or 1
    pool = ThreadPoolExecutor(max_workers=num_cores)
    loop = asyncio.get_event_loop()
    loop.set_default_executor(pool)
    logger.info(f"Thread pool with {num_cores} workers configured")

    # Load models
    load_models()

    try:
        yield
    finally:
        MODEL_REGISTRY.clear()
        logger.info("Model registry cleared on shutdown")
        pool.shutdown(wait=True)
        logger.info("Thread pool shut down")

app.router.lifespan_context = lifespan

# ==================
# VERSIONED ROUTES
# ==================

app.include_router(health.router, prefix=f"{API_VERSION}/health", tags=["Health"])
app.include_router(predict.router, prefix=f"{API_VERSION}/predict", tags=["Predict"])
app.include_router(jobs.router, prefix=f"{API_VERSION}/jobs", tags=["Jobs"])
app.include_router(models.router, prefix=f"{API_VERSION}/models", tags=["Models"])

# ==================
# STATIC INDEX
# ==================

@app.get("/")
def read_index():
    return FileResponse("static/index.html")
