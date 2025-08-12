import time
import os
from celery import Celery
import pandas as pd
import joblib
from shared.state import MODEL_REGISTRY
from settings import settings  
from shared.utils import preprocess_input
from shared.load_models import load_models

# -------------------------------------------------------------
# Initialize the Celery app using broker URL from settings
# -------------------------------------------------------------

celery_app = Celery(
    "model_tasks",
    broker=settings.broker_url,      # Pulled from .env or env vars
    backend=settings.broker_url      # Optional: same Redis for backend
)



# -------------------------------------------------------------
# Load models into memory for async use.
# This ensures models are only loaded once when the worker starts,
# instead of loading them every time a task is run.
# -------------------------------------------------------------
load_models()

@celery_app.task(name="ping")
def ping():
    """
    Simple ping task to confirm Celery worker is alive.

    Used by the `/ready` health check endpoint to verify that
    the worker is running and connected to Redis.

    Returns:
    --------
    str
        A fixed "Ready!" string indicating health.
    """
    return "Ready!"


@celery_app.task(name="run_async_inference")
def run_async_inference(model_id: str, features: list[dict], user_id: str):
    """
    Run an asynchronous prediction task using a registered model.

    This function is executed in the background via Celery. It transforms
    input features into a DataFrame, runs the model prediction, and returns
    the result in a structured format.

    Parameters:
    -----------
    model_id : str
        The ID of the model to use for prediction (must exist in MODEL_REGISTRY).

    features : list[dict]
        A list of input dictionaries, each representing one feature row.

    user_id : str
        ID of the user that submitted the job.

    Returns:
    --------
    dict
        A structured result object containing predictions and metadata like runtime.

    Raises:
    -------
    ValueError
        If the specified model is not found in the registry.
    """
    artifacts = MODEL_REGISTRY.get(model_id)

    if not artifacts:
        raise ValueError(f"Model '{model_id}' not found in registry")
    
    df = preprocess_input(features, artifacts)

    # Run prediction and track runtime
    start = time.time()
    predictions = artifacts["model"].predict(df).tolist()
    end = time.time()
    duration_ms = round((end - start) * 1000, 3)

    return {
        "user_id": user_id,
        "job_id": None,  # The actual job ID is set externally by the caller
        "model_id": model_id,
        "status": "SUCCESS",
        "result": {
            "predictions": predictions,
            "duration_ms": duration_ms,
            "additional_info": {
                "num_inputs": len(features)
            }
        }
    }
