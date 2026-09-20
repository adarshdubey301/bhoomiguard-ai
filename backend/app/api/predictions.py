"""
BhoomiGuard AI — Prediction History API
GET /api/predictions — paginated prediction history with search/filter
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database.db import get_db
from app.models.database import Prediction
from app.api.auth import get_current_user
from app.models.database import User

router = APIRouter(prefix="/api", tags=["Predictions"])
logger = logging.getLogger(__name__)


@router.get("/predictions")
def get_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    prediction: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return paginated prediction history with optional filtering.
    Supports: search (project_id/district), district filter, risk_level, prediction (Yes/No), stage.
    """
    query = db.query(Prediction)

    if search:
        query = query.filter(
            or_(
                Prediction.project_id.ilike(f"%{search}%"),
                Prediction.district.ilike(f"%{search}%"),
            )
        )
    if district:
        query = query.filter(Prediction.district == district)
    if risk_level:
        query = query.filter(Prediction.risk_level == risk_level)
    if prediction:
        query = query.filter(Prediction.prediction == prediction)
    if stage:
        query = query.filter(Prediction.current_stage == stage)

    total = query.count()
    records = query.order_by(desc(Prediction.created_at)).offset(skip).limit(limit).all()

    result = []
    for r in records:
        result.append({
            "id": r.id,
            "project_id": r.project_id,
            "district": r.district,
            "current_stage": r.current_stage,
            "prediction": r.prediction,
            "delay_probability": round(r.delay_probability, 4),
            "risk_level": r.risk_level,
            "model_name": r.model_name,
            "model_version": r.model_version,
            "top_risk_factors": json.loads(r.top_risk_factors or "[]"),
            "recommendations": json.loads(r.recommendations or "[]"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"total": total, "skip": skip, "limit": limit, "predictions": result}


@router.get("/predictions/{prediction_id}")
def get_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single prediction record by ID."""
    record = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {
        "id": record.id,
        "project_id": record.project_id,
        "district": record.district,
        "current_stage": record.current_stage,
        "prediction": record.prediction,
        "delay_probability": record.delay_probability,
        "risk_level": record.risk_level,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "top_risk_factors": json.loads(record.top_risk_factors or "[]"),
        "recommendations": json.loads(record.recommendations or "[]"),
        "input_features": json.loads(record.input_features or "{}"),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
