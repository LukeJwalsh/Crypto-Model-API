from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class PredictionRequest(BaseModel):
    model_id: str
    inputs: List[Dict[str, float]]


class PredictionResult(BaseModel):
    predictions: List[float]
    duration_ms: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None


class PredictionResponse(BaseModel):
    user_id: str
    model_id: str
    result: PredictionResult


class AsyncPredictionResponse(BaseModel):
    user_id: str
    job_id: str
    model_id: str
    status: str


class AsyncResultResponse(BaseModel):
    user_id: str
    job_id: str
    model_id: str
    status: str
    result: PredictionResult


class ModelSummary(BaseModel):
    model_id: str
    name: str
    description: str


class ModelMetaData(BaseModel):
    model_id: str
    name: str
    description: str
    version: str
    created_at: datetime
    schema_: Dict[str, List[str]]