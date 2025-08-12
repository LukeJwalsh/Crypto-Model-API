from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from shared.worker import celery_app
from shared.state import MODEL_REGISTRY

router = APIRouter()


@router.get("/", tags=["Health"])
def health_root() -> Response:
    """
    Root health endpoint.

    Simple health check for confirming the API is reachable.
    Does not verify model or worker readiness — only confirms HTTP access.

    Returns:
    --------
    JSONResponse
        Status 200 with a basic confirmation message.
    """
    return JSONResponse(status_code=200, content={'status': 'Health root endpoint'})


@router.get("/live", tags=["Health"])
def check_server() -> Response:
    """
    Liveness probe.

    Verifies the server process is up and responsive to HTTP requests.
    Used by infrastructure tools like Kubernetes to check if the app is alive.

    Returns:
    --------
    JSONResponse
        Status 200 with a confirmation of liveliness.
    """
    return JSONResponse(
        status_code=200,
        content={'status': 'alive'},
        headers={'Cache-Control': 'no-cache'}
    )


@router.get("/ready", tags=["Health"])
def check_server_ready() -> Response:
    """
    Readiness probe.

    Confirms the server is ready to serve requests:
    - Ensures that at least one model is loaded in the in-memory registry.
    - Verifies that the Celery worker is responsive.

    Returns:
    --------
    JSONResponse
        Status 200 if ready, 503 if not ready (e.g., no models or unresponsive Celery worker).

    Raises:
    -------
    HTTPException
        503 if either models are not loaded or Celery is not responding.
    """
    # Check that the model registry is populated
    if not MODEL_REGISTRY:
        raise HTTPException(status_code=503, detail="Models not loaded")

    # Check that Celery worker is responsive via a "ping" task
    try:
        result = celery_app.send_task("ping")
        if result.get(timeout=5) != "Ready!":
            raise HTTPException(status_code=503, detail="Celery is unavailable")
    except Exception:
        raise HTTPException(status_code=503, detail="Celery is unavailable")

    return JSONResponse(
        status_code=200,
        content={'status': 'ready'},
        headers={'Cache-Control': 'no-cache'}
    )
