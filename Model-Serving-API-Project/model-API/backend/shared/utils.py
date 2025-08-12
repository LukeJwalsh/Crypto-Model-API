import pandas as pd
from fastapi import HTTPException
from typing import List, Dict, Any

def preprocess_input(
    raw_inputs: List[Dict[str, Any]], 
    artifacts: Dict[str, Any]
) -> pd.DataFrame:
    """
    Given a list of dicts (one per record) and your artifacts dict,
    returns a DataFrame ready for model.predict().

    Steps:
    1. Build DataFrame and ensure all expected features are present.
    2. Clip outliers by lower_bounds / upper_bounds.
    3. Apply scaler.transform to normalize.
    """
    feature_names = artifacts["feature_names"]
    
    # 1. Load into DF and check for missing columns
    df = pd.DataFrame(raw_inputs)
    missing = set(feature_names) - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422, 
            detail=f"Missing features: {', '.join(sorted(missing))}"
        )

    # 2. Reorder & winsorize
    df = df[feature_names]
    lower = artifacts["lower_bounds"]
    upper = artifacts["upper_bounds"]
    df = df.clip(lower=lower, upper=upper, axis=1)

    # 3. Scale
    scaler = artifacts["scaler"]
    scaled_array = scaler.transform(df)
    return pd.DataFrame(scaled_array, columns=feature_names)
