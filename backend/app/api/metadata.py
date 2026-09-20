"""
BhoomiGuard AI — Metadata API
Provides districts, stages, and configuration from the actual CSV dataset.
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.schemas.schemas import MetadataResponse
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["Metadata"])
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATASET_PATH = BASE_DIR / "data" / "land_acquisition_delay_dataset_10000.csv"
METADATA_PATH = BASE_DIR / "backend" / "models_store" / "model_metadata.json"

# Cache
_metadata_cache: dict | None = None


def _load_from_model_metadata() -> dict | None:
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _load_from_csv() -> dict:
    try:
        import pandas as pd
        df = pd.read_csv(DATASET_PATH)
        return {
            "districts": sorted(df["district"].dropna().unique().tolist()),
            "current_stages": sorted(df["current_stage"].dropna().unique().tolist()),
            "total_records": len(df),
        }
    except Exception as e:
        logger.error(f"Failed to read CSV for metadata: {e}")
        return {"districts": [], "current_stages": [], "total_records": 0}


@router.get("/metadata", response_model=MetadataResponse)
def get_metadata():
    """
    Return available districts, stages, risk thresholds.
    Districts and stages come from the actual CSV / model training metadata.
    """
    global _metadata_cache

    if _metadata_cache:
        return _metadata_cache

    # Try model metadata first (most accurate — from training data)
    model_meta = _load_from_model_metadata()
    if model_meta and model_meta.get("districts"):
        result = MetadataResponse(
            districts=model_meta["districts"],
            current_stages=model_meta["stages"],
            risk_thresholds={
                "Low": {"min": 0, "max": settings.RISK_LOW_MAX},
                "Medium": {"min": settings.RISK_LOW_MAX, "max": settings.RISK_MEDIUM_MAX},
                "High": {"min": settings.RISK_MEDIUM_MAX, "max": settings.RISK_HIGH_MAX},
                "Critical": {"min": settings.RISK_HIGH_MAX, "max": 1.0},
                "note": "Operational risk bands — not official government classifications",
            },
            total_records=model_meta.get("dataset_size", 0),
        )
    else:
        # Fallback: read directly from CSV
        csv_data = _load_from_csv()
        result = MetadataResponse(
            districts=csv_data["districts"],
            current_stages=csv_data["current_stages"],
            risk_thresholds={
                "Low": {"min": 0, "max": settings.RISK_LOW_MAX},
                "Medium": {"min": settings.RISK_LOW_MAX, "max": settings.RISK_MEDIUM_MAX},
                "High": {"min": settings.RISK_MEDIUM_MAX, "max": settings.RISK_HIGH_MAX},
                "Critical": {"min": settings.RISK_HIGH_MAX, "max": 1.0},
                "note": "Operational risk bands — not official government classifications",
            },
            total_records=csv_data["total_records"],
        )

    _metadata_cache = result.model_dump()
    return result
