# shared package with modules to be able to be imported directly from shared if desired
from .worker import celery_app
from .state import MODEL_REGISTRY
from .logger_config import logger