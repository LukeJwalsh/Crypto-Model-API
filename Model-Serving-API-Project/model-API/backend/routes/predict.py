from fastapi import APIRouter, Security, status, HTTPException
import time
from schema import PredictionResponse, PredictionRequest, PredictionResult
from middleware.auth import get_current_user_with_scopes
from shared.state import MODEL_REGISTRY
from shared import logger
from shared.utils import preprocess_input
from models import MODELS  

router = APIRouter()

@router.post("/", response_model=PredictionResponse, tags=["Predict"])
def model_predict(
    request: PredictionRequest,
    user: dict = Security(get_current_user_with_scopes, scopes=["predictions:create"])
):
    try:
        model_id = request.model_id
        user_id = user["sub"]

        logger.info(f"Prediction request for model '{model_id}' from user '{user_id}'")

        # 1) Ensure artifacts are loaded
        artifacts = MODEL_REGISTRY.get(model_id)
        if not artifacts:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

        # 2) Check model metadata from static MODELS dict
        metadata = MODELS.get(model_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Model metadata not found")

        if metadata["type"] != "sync":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not synchronous"
            )

        # 3) Prepare raw inputs and preprocess dynamically
        raw_inputs = request.inputs
        X_input = preprocess_input(raw_inputs, artifacts)

        # 4) Run prediction & measure duration
        start = time.time()
        preds = artifacts["model"].predict(X_input).tolist()
        duration = round((time.time() - start) * 1000, 3)

        # 5) Build result object
        result = PredictionResult(
            predictions=preds,
            duration_ms=duration,
            additional_info={"num_inputs": len(raw_inputs)}
        )

        return {
            "user_id": user_id,
            "model_id": model_id,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during prediction", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
