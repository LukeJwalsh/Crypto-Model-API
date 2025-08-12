import os
import joblib

from shared.state import MODEL_REGISTRY
from models import MODELS
from settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def load_models():
    import pathlib
    base = pathlib.Path(__file__).parent.parent
    for name, metadata in MODELS.items():
        try: 
            fn = metadata["filename"]
            path = os.path.join(base, settings.model_dir, fn)
            artifacts = joblib.load(path)
            artifacts["metadata"] = metadata
            MODEL_REGISTRY[name] = artifacts
        except Exception as e:
            logger.error(f"Failed to load model {name}: {e}")
    logger.info(f"Models loaded into registry {list(MODEL_REGISTRY.keys())}")