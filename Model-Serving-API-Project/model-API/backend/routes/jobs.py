from fastapi import APIRouter, Security, HTTPException, status
from typing import Dict, Any, cast
from middleware.auth import get_current_user_with_scopes
from celery.result import AsyncResult as CeleryAsyncResult

from schema import (
    AsyncPredictionResponse,
    PredictionRequest,
    AsyncResultResponse,
    PredictionResult,
)
from shared.state import MODEL_REGISTRY
from shared.worker import celery_app
from shared.utils import preprocess_input
from shared import logger

router = APIRouter()


@router.post("/", response_model=AsyncPredictionResponse, status_code=202, tags=["Jobs"])
async def send_async_job(
    request: PredictionRequest,
    user: dict = Security(get_current_user_with_scopes, scopes=["predictions:create"])
):
    """
    Submit an asynchronous prediction job using a Celery worker.

    Security:
    ---------
    Requires a valid JWT with the `predictions:create` scope.

    Steps:
    ------
    1. Load model artifacts (model, scaler, bounds, feature_names).
    2. Dynamically preprocess incoming JSON via `preprocess_input`.
    3. Dispatch processed features + metadata to Celery.
    """
    try:
        model_id = request.model_id
        user_id = user["sub"]
        logger.info(f"Async prediction request for model '{model_id}' by user '{user_id}'")

        # 1) Load and type-cast artifacts
        raw = MODEL_REGISTRY.get(model_id)
        if raw is None:
            raise HTTPException(status_code=404, detail="Model not found")
        artifacts: Dict[str, Any] = cast(Dict[str, Any], raw)
        logger.info(f"Artifacts loaded for model '{model_id}': {artifacts}")
        # 2) Ensure this model supports async jobs
        metadata = artifacts.get("metadata", {})  

        if metadata.get("type") != "async":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not asynchronous"
            )

        # 3) Preprocess input dynamically
        raw_inputs = request.inputs
        X_processed = preprocess_input(raw_inputs, artifacts)

        # Convert to JSON-serializable records for Celery
        feature_payload = X_processed.to_dict(orient="records")

        # 4) Dispatch to Celery
        job = celery_app.send_task(
            "run_async_inference",
            args=[model_id, feature_payload, user_id]
        )

        return {
            "user_id": user_id,
            "job_id": job.id,
            "model_id": model_id,
            "status": "PENDING",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during async prediction", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# We might need to set scope restriction here?
@router.get("/{job_id}", response_model=AsyncResultResponse, tags=["Jobs"])
async def get_prediction(
    job_id: str,
    user: dict = Security(get_current_user_with_scopes, scopes=["predictions:read"])
):
    """
    Poll the status or result of a previously submitted async prediction job.

    Security:
    ---------
    Requires a valid JWT with the `predictions:read` scope.

    Returns:
    --------
    - 202 if still pending/started/retried
    - 500 if failed or malformed
    - 200 with `PredictionResult` if successful
    """

    try:
        result = CeleryAsyncResult(job_id)

        # We may want to remove this as I believe AsyncResult always returns something?
        if not result:
            raise HTTPException(404, detail="Job ID not found")

        status_str = result.status
        if status_str in ("PENDING", "STARTED", "RETRY"):
            raise HTTPException(status_code=202, detail="Job is still in progress")
        if status_str == "FAILURE":
            raise HTTPException(status_code=500, detail=f"Job failed: {result.result}")
        
        if status_str == "SUCCESS":
            raw = result.result
            parsed = PredictionResult(**raw["result"])
            return {
                "user_id": raw["user_id"],
                "job_id": job_id,
                "model_id": raw["model_id"],
                "status": raw["status"],
                "result": parsed,
            }

        raise HTTPException(status_code=500, detail=f"Unhandled job status: {status_str}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error parsing async job result", exc_info=True)
        raise HTTPException(status_code=500, detail="Malformed async result structure")
