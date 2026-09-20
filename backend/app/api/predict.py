"""
BhoomiGuard AI — Prediction API
POST /api/predict — runs ML prediction, SHAP, and recommendations.
"""
import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.database import Prediction
from app.schemas.schemas import PredictionInputWithId, PredictionResponse, RiskFactor, Recommendation
from app.services import ml_service, shap_service, recommendation as rec_service
from app.core.config import get_risk_level
from app.api.auth import get_current_user
from app.models.database import User

router = APIRouter(prefix="/api", tags=["Prediction"])
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictionResponse)
def predict_delay(
    request: PredictionInputWithId,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Predict whether a land acquisition project will be delayed.
    
    Input: 14 project characteristics (NO delay_status, NO project_id as feature).
    Output: probability, prediction, risk level, SHAP explanation, recommendations.
    """
    if not ml_service.is_model_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model is not available. Please run the training pipeline first.",
        )

    # Generate project_id if not provided
    project_id = request.project_id or f"PRJ-{uuid.uuid4().hex[:8].upper()}"

    # Build feature dict (explicitly exclude delay_status and project_id)
    input_features = {
        "district": request.district,
        "total_land_parcels": request.total_land_parcels,
        "acquired_land_parcels": request.acquired_land_parcels,
        "pending_land_parcels": request.pending_land_parcels,
        "total_landowners": request.total_landowners,
        "compensation_pending": request.compensation_pending,
        "legal_cases": request.legal_cases,
        "documents_pending": request.documents_pending,
        "approval_pending_days": request.approval_pending_days,
        "objections_count": request.objections_count,
        "survey_completed_percent": request.survey_completed_percent,
        "current_stage": request.current_stage,
        "previous_delay_days": request.previous_delay_days,
        "land_pending_percent": request.land_pending_percent,
        # delay_status intentionally NOT present ✓
    }

    try:
        # Run prediction
        result = ml_service.predict(input_features)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to generate prediction. Please verify the project information and try again.",
        )

    delay_probability = result["delay_probability"]
    prediction_label = result["prediction"]
    risk_level = get_risk_level(delay_probability)
    model_name = result["model_name"]
    model_version = result["model_version"]
    df_input = result["df_input"]
    unknown_warning = result.get("unknown_district_warning")

    # Load model pipeline for SHAP
    try:
        import joblib
        from pathlib import Path
        model_pipeline = joblib.load(
            Path(__file__).resolve().parent.parent.parent.parent / "backend" / "models_store" / "production_model.joblib"
        )
        shap_factors = shap_service.get_shap_explanation(model_pipeline, df_input, top_n=7)
    except Exception as e:
        logger.warning(f"SHAP failed, using empty factors: {e}")
        shap_factors = []

    # Get district context from dataset
    district_context = _get_district_context(request.district, db)

    # Generate recommendations
    district_delay_rate = district_context.get("delay_rate") if district_context else None
    recommendations = rec_service.generate_recommendations(
        input_features=input_features,
        top_risk_factors=shap_factors,
        risk_level=risk_level,
        district_delay_rate=district_delay_rate,
    )

    # Save to database
    try:
        pred_record = Prediction(
            project_id=project_id,
            district=request.district,
            current_stage=request.current_stage,
            prediction=prediction_label,
            delay_probability=delay_probability,
            risk_level=risk_level,
            model_name=model_name,
            model_version=model_version,
            top_risk_factors=json.dumps(shap_factors),
            recommendations=json.dumps(recommendations),
            input_features=json.dumps(input_features),
            created_by=current_user.id,
        )
        db.add(pred_record)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save prediction to DB: {e}")

    return PredictionResponse(
        prediction=prediction_label,
        delay_probability=delay_probability,
        risk_level=risk_level,
        district=request.district,
        current_stage=request.current_stage,
        model_name=model_name,
        model_version=model_version,
        top_risk_factors=[RiskFactor(**f) for f in shap_factors],
        recommendations=[Recommendation(**r) for r in recommendations],
        district_context=district_context,
        unknown_district_warning=unknown_warning,
    )


def _get_district_context(district: str, db: Session) -> dict | None:
    """Calculate district-level historical stats from the dataset."""
    try:
        import pandas as pd
        from pathlib import Path
        dataset_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "land_acquisition_delay_dataset_10000.csv"
        if not dataset_path.exists():
            return None
        df = pd.read_csv(dataset_path)
        ddf = df[df["district"] == district]
        if ddf.empty:
            return None
        total = len(ddf)
        delayed = (ddf["delay_status"].str.lower() == "yes").sum()
        return {
            "district": district,
            "total_projects": int(total),
            "delayed_projects": int(delayed),
            "delay_rate": float(round(delayed / total, 4)) if total > 0 else 0.0,
            "avg_pending_land": float(round(ddf["land_pending_percent"].mean(), 2)),
            "avg_approval_pending": float(round(ddf["approval_pending_days"].mean(), 1)),
            "avg_legal_cases": float(round(ddf["legal_cases"].mean(), 1)),
            "avg_compensation_pending": float(round(ddf["compensation_pending"].mean(), 1)),
        }
    except Exception as e:
        logger.warning(f"Could not get district context: {e}")
        return None
