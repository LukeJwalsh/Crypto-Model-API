from fastapi import APIRouter, Security, HTTPException, status
from middleware.auth import get_current_user_with_scopes
from schema import ModelMetaData
from models import MODELS
from shared import logger

router = APIRouter()

@router.get("/", tags=["Models"])
def model_menu(
    user: dict = Security(get_current_user_with_scopes, scopes=["models:list"])
):
    """
    Retrieve a summary list of all available models (requires 'models:list' scope).

    Returns:
    --------
    list[dict]
        A list of dictionaries summarizing each registered model's ID, name, type, and description.

    Security:
    ---------
    Requires a valid JWT with the `models:list` scope.

    Parameters:
    -----------
    user : dict
        The authenticated user extracted from the JWT.
    """
    try:
        return [
            {
                "model_id": model["model_id"],
                "name": model["name"],
                "description": model["description"],
                "type": model["type"]
            }
            for model in MODELS.values()
        ]
    except Exception as e:
        logger.exception("Error retrieving model list", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch model list")



@router.get("/{model_id}", response_model=ModelMetaData, tags=["Models"])
async def get_model_metadata(
    model_id: str,
    user: dict = Security(get_current_user_with_scopes, scopes=["models:read"])
):
    """
    Retrieve detailed metadata for a specific model (requires 'models:read' scope).

    Parameters:
    -----------
    model_id : str
        The ID of the model to retrieve metadata for.

    user : dict
        The authenticated user (used for authorization, injected via JWT Security).

    Returns:
    --------
    ModelMetaData
        A fully structured metadata object describing the model.

    Raises:
    -------
    HTTPException
        - 404: If model not found
        - 500: Internal server error
    """
    try:
        model = MODELS.get(model_id)
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
        return model
    except Exception as e:
        logger.exception("Error retrieving model metadata", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch model data")