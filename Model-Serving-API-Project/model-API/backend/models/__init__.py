#List of our models, Sync models can be done synchronously, Async models must use Aysnchronous prediction
from datetime import datetime
from typing import Any, Dict, List, TypedDict

# Add more models when we have them

class ModelInfo(TypedDict):
    model_id: str
    name: str
    description: str
    version: str
    created_at: str
    schema_: Dict[str, List[str]]
    type: str
    filename: str

MODELS: Dict[str, ModelInfo] = {
    "xgb_momentum": {
        "model_id": "xgb_momentum",
        "name": "XGBoost Momentum Model",
        "description": "Predicts 7-day forward returns using technical indicators and market-neutral features.",
        "version": "1.0",
        "created_at": datetime(2025, 7, 18).isoformat(),
        "schema_": {
            "required_features": [
                "ret_7d", "ret_10d", "ret_14d", "ret_21d", "ret_30d", "ret_42d", "ret_60d",
                "volatility_14d", "volume_zscore_14d", "rsi_14", "bb_width", "bb_percent_b", "macd_diff",
                "mom_x_vol_42d",
                "ret_1d_neutral", "ret_7d_neutral", "ret_10d_neutral", "ret_14d_neutral",
                "ret_21d_neutral", "ret_30d_neutral", "ret_42d_neutral", "ret_60d_neutral"
            ]
        },
        "type": "sync",
        "filename": "model_artifacts.pkl"
    },
    "xgb_momentum_async": {
        "model_id": "xgb_momentum_async",
        "name": "XGBoost Momentum Model but async",
        "description": "Predicts 7-day forward returns using technical indicators and market-neutral features. Same as the xgb_momentum just classified as an async model for testing.",
        "version": "1.0",
        "created_at": datetime(2025, 7, 18).isoformat(),
        "schema_": {
            "required_features": [
                "ret_7d", "ret_10d", "ret_14d", "ret_21d", "ret_30d", "ret_42d", "ret_60d",
                "volatility_14d", "volume_zscore_14d", "rsi_14", "bb_width", "bb_percent_b", "macd_diff",
                "mom_x_vol_42d",
                "ret_1d_neutral", "ret_7d_neutral", "ret_10d_neutral", "ret_14d_neutral",
                "ret_21d_neutral", "ret_30d_neutral", "ret_42d_neutral", "ret_60d_neutral"
            ]
        },
        "type": "async",
        "filename": "model_artifacts.pkl"
    }
}
