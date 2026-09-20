"""
BhoomiGuard AI — Analytics API
Dataset-driven analytics: overview, district stats, stage distribution, risk distribution.
All values calculated dynamically from the actual CSV dataset.
"""
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException

from app.schemas.schemas import OverviewStats, DistrictStats, StageDistribution, RiskDistribution
from app.api.auth import get_current_user
from app.models.database import User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATASET_PATH = BASE_DIR / "data" / "land_acquisition_delay_dataset_10000.csv"

_df_cache = None


def _get_df():
    global _df_cache
    if _df_cache is None:
        import pandas as pd
        if not DATASET_PATH.exists():
            raise HTTPException(status_code=503, detail="Dataset not found")
        _df_cache = pd.read_csv(DATASET_PATH)
    return _df_cache


@router.get("/overview")
def get_overview(
    district: Optional[str] = Query(None, description="Filter by district"),
    stage: Optional[str] = Query(None, description="Filter by current stage"),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard summary statistics.
    All values calculated from actual CSV data.
    High-risk and Critical counts come from DB prediction history.
    """
    import pandas as pd
    from app.database.db import SessionLocal
    from app.models.database import Prediction

    df = _get_df().copy()
    if district and district != "All Districts":
        df = df[df["district"] == district]
    if stage and stage != "All Stages":
        df = df[df["current_stage"] == stage]

    total = len(df)
    delayed = int((df["delay_status"].str.lower() == "yes").sum())
    non_delayed = total - delayed
    delay_rate = round(delayed / total, 4) if total > 0 else 0.0

    # High/Critical from prediction DB
    db = SessionLocal()
    try:
        pred_query = db.query(Prediction)
        if district and district != "All Districts":
            pred_query = pred_query.filter(Prediction.district == district)
        if stage and stage != "All Stages":
            pred_query = pred_query.filter(Prediction.current_stage == stage)
        high_risk = pred_query.filter(Prediction.risk_level == "High").count()
        critical = pred_query.filter(Prediction.risk_level == "Critical").count()
        total_preds = pred_query.count()
    finally:
        db.close()

    return {
        "total_projects": total,
        "delayed_projects": delayed,
        "non_delayed_projects": non_delayed,
        "delay_rate": delay_rate,
        "high_risk_predictions": high_risk,
        "critical_predictions": critical,
        "total_predictions": total_preds,
        "district": district,
        "stage": stage,
        "avg_pending_land": round(df["land_pending_percent"].mean(), 2) if total > 0 else 0,
        "avg_approval_pending": round(df["approval_pending_days"].mean(), 1) if total > 0 else 0,
        "avg_legal_cases": round(df["legal_cases"].mean(), 1) if total > 0 else 0,
        "avg_compensation_pending": round(df["compensation_pending"].mean(), 1) if total > 0 else 0,
    }


@router.get("/districts")
def get_district_analytics(current_user: User = Depends(get_current_user)):
    """
    Per-district statistics sorted by delay rate (highest first).
    Used for the district leaderboard and comparison chart.
    """
    df = _get_df().copy()
    results = []
    rank = 1
    district_groups = df.groupby("district")

    for district, group in district_groups:
        total = len(group)
        delayed = int((group["delay_status"].str.lower() == "yes").sum())
        delay_rate = round(delayed / total, 4) if total > 0 else 0.0
        results.append({
            "district": district,
            "total_projects": total,
            "delayed_projects": delayed,
            "delay_rate": delay_rate,
            "delay_rate_pct": round(delay_rate * 100, 2),
            "avg_pending_land": round(group["land_pending_percent"].mean(), 2),
            "avg_approval_pending": round(group["approval_pending_days"].mean(), 1),
            "avg_legal_cases": round(group["legal_cases"].mean(), 1),
            "avg_compensation_pending": round(group["compensation_pending"].mean(), 1),
        })

    results.sort(key=lambda x: x["delay_rate"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {"districts": results, "total_districts": len(results)}


@router.get("/district/{district_name}")
def get_district_detail(district_name: str, current_user: User = Depends(get_current_user)):
    """Detailed analytics for a specific district."""
    df = _get_df().copy()
    ddf = df[df["district"] == district_name]
    if ddf.empty:
        raise HTTPException(status_code=404, detail=f"District '{district_name}' not found in dataset")

    total = len(ddf)
    delayed = int((ddf["delay_status"].str.lower() == "yes").sum())

    # Stage distribution
    stage_dist = []
    for stage, grp in ddf.groupby("current_stage"):
        sc = len(grp)
        sd = int((grp["delay_status"].str.lower() == "yes").sum())
        stage_dist.append({
            "stage": stage,
            "count": sc,
            "delayed": sd,
            "delay_rate": round(sd / sc, 4) if sc > 0 else 0,
        })

    return {
        "district": district_name,
        "total_projects": total,
        "delayed_projects": delayed,
        "non_delayed_projects": total - delayed,
        "delay_rate": round(delayed / total, 4) if total > 0 else 0,
        "avg_pending_land": round(ddf["land_pending_percent"].mean(), 2),
        "avg_approval_pending": round(ddf["approval_pending_days"].mean(), 1),
        "avg_legal_cases": round(ddf["legal_cases"].mean(), 1),
        "avg_compensation_pending": round(ddf["compensation_pending"].mean(), 1),
        "avg_documents_pending": round(ddf["documents_pending"].mean(), 1),
        "avg_objections": round(ddf["objections_count"].mean(), 1),
        "stage_distribution": stage_dist,
    }


@router.get("/stages")
def get_stage_distribution(
    district: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Stage-wise delay distribution."""
    df = _get_df().copy()
    if district and district != "All Districts":
        df = df[df["district"] == district]

    results = []
    for stage, grp in df.groupby("current_stage"):
        sc = len(grp)
        sd = int((grp["delay_status"].str.lower() == "yes").sum())
        results.append({
            "stage": stage,
            "count": sc,
            "delayed": sd,
            "non_delayed": sc - sd,
            "delay_rate": round(sd / sc, 4) if sc > 0 else 0,
        })
    return {"stages": results}


@router.get("/risk-distribution")
def get_risk_distribution(
    district: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Risk level distribution from prediction history."""
    from app.database.db import SessionLocal
    from app.models.database import Prediction

    db = SessionLocal()
    try:
        query = db.query(Prediction)
        if district and district != "All Districts":
            query = query.filter(Prediction.district == district)
        total = query.count()
        risk_counts = {}
        for level in ["Low", "Medium", "High", "Critical"]:
            risk_counts[level] = query.filter(Prediction.risk_level == level).count()
    finally:
        db.close()

    result = []
    for level, count in risk_counts.items():
        result.append({
            "risk_level": level,
            "count": count,
            "percentage": round(count / total * 100, 2) if total > 0 else 0,
        })
    return {"risk_distribution": result, "total_predictions": total}


@router.get("/feature-importance")
def get_feature_importance(current_user: User = Depends(get_current_user)):
    """Aggregate feature importance from the trained model."""
    import json
    from pathlib import Path
    import joblib
    import numpy as np

    model_path = BASE_DIR / "backend" / "models_store" / "production_model.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="Model not available")

    try:
        pipeline = joblib.load(model_path)
        classifier = pipeline.named_steps["classifier"]
        preprocessor = pipeline.named_steps["preprocessor"]

        feature_names = []
        for name, transformer, cols in preprocessor.transformers_:
            if name == "numerical":
                feature_names.extend(cols)
            elif name == "categorical":
                ohe = transformer.named_steps.get("onehot")
                if ohe is not None and hasattr(ohe, "get_feature_names_out"):
                    feature_names.extend(ohe.get_feature_names_out(cols).tolist())
                else:
                    feature_names.extend(cols)

        if hasattr(classifier, "feature_importances_"):
            importances = classifier.feature_importances_
        elif hasattr(classifier, "coef_"):
            importances = np.abs(classifier.coef_[0])
        else:
            return {"feature_importance": []}

        # Aggregate OHE features back
        aggregated = {}
        original_cols = [
            "total_land_parcels", "acquired_land_parcels", "pending_land_parcels",
            "total_landowners", "compensation_pending", "legal_cases", "documents_pending",
            "approval_pending_days", "objections_count", "survey_completed_percent",
            "previous_delay_days", "land_pending_percent", "district", "current_stage",
        ]
        for fname, imp in zip(feature_names, importances):
            matched = next((c for c in original_cols if fname.startswith(f"{c}_") or fname == c), fname)
            aggregated[matched] = aggregated.get(matched, 0) + float(imp)

        result = [{"feature": k, "importance": round(v, 4)} for k, v in aggregated.items()]
        result.sort(key=lambda x: x["importance"], reverse=True)
        return {"feature_importance": result}
    except Exception as e:
        logger.error(f"Feature importance error: {e}")
        raise HTTPException(status_code=500, detail="Could not compute feature importance")
