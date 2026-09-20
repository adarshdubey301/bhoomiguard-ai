"""
BhoomiGuard AI — ML Service
Loads the trained production model, runs predictions, computes SHAP values.
"""
import json
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # project root
MODELS_DIR = BASE_DIR / "backend" / "models_store"
PRODUCTION_MODEL_PATH = MODELS_DIR / "production_model.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
COMPARISON_PATH = MODELS_DIR / "model_comparison.json"

FEATURE_COLUMNS = [
    "district", "total_land_parcels", "acquired_land_parcels", "pending_land_parcels",
    "total_landowners", "compensation_pending", "legal_cases", "documents_pending",
    "approval_pending_days", "objections_count", "survey_completed_percent",
    "current_stage", "previous_delay_days", "land_pending_percent",
]

_model = None
_metadata = None
_comparison = None


def _load_model():
    global _model
    if _model is None:
        if not PRODUCTION_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Production model not found at {PRODUCTION_MODEL_PATH}. "
                "Please run: python ml/train.py"
            )
        _model = joblib.load(PRODUCTION_MODEL_PATH)
        logger.info(f"Model loaded from {PRODUCTION_MODEL_PATH}")
    return _model


def _load_metadata() -> dict:
    global _metadata
    if _metadata is None:
        if not METADATA_PATH.exists():
            raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}. Run training first.")
        with open(METADATA_PATH) as f:
            _metadata = json.load(f)
    return _metadata


def _load_comparison() -> list:
    global _comparison
    if _comparison is None:
        if not COMPARISON_PATH.exists():
            return []
        with open(COMPARISON_PATH) as f:
            _comparison = json.load(f)
    return _comparison


def is_model_ready() -> bool:
    return PRODUCTION_MODEL_PATH.exists() and METADATA_PATH.exists()


def reload_model():
    """Force-reload model and metadata after retraining."""
    global _model, _metadata, _comparison
    _model = None
    _metadata = None
    _comparison = None


def get_metadata() -> dict:
    return _load_metadata()


def get_comparison() -> list:
    return _load_comparison()


def predict(input_data: dict, known_districts: Optional[list] = None) -> dict:
    """
    Run delay prediction.
    Returns probability, prediction label, and raw feature array.
    delay_status is intentionally EXCLUDED from input_data.
    """
    model = _load_model()
    meta = _load_metadata()

    # Build DataFrame with correct column order
    df_input = pd.DataFrame([{col: input_data[col] for col in FEATURE_COLUMNS}])

    # Recalculate derived features on backend (don't trust frontend)
    total = df_input["total_land_parcels"].iloc[0]
    acquired = df_input["acquired_land_parcels"].iloc[0]
    pending = max(0, total - acquired)
    df_input["pending_land_parcels"] = pending
    df_input["land_pending_percent"] = round((pending / total) * 100, 2) if total > 0 else 0.0

    # Check for unknown district
    district = input_data.get("district", "")
    unknown_warning = None
    training_districts = meta.get("districts", [])
    if training_districts and district not in training_districts:
        unknown_warning = (
            f"District '{district}' was not present in training data. "
            "Prediction may have reduced reliability."
        )
        logger.warning(unknown_warning)

    # Predict
    prob = float(model.predict_proba(df_input)[0][1])
    pred_label = "Yes" if prob >= 0.5 else "No"

    return {
        "delay_probability": round(prob, 4),
        "prediction": pred_label,
        "df_input": df_input,
        "unknown_district_warning": unknown_warning,
        "model_name": meta["model_name"],
        "model_version": meta["model_version"],
    }
