"""
BhoomiGuard AI — Model Management API
GET  /api/model/metrics    — current production model performance
GET  /api/model/comparison — all models comparison
GET  /api/model/history    — model version history from DB
POST /api/model/retrain    — trigger retraining
"""
import json
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.database import ModelVersion
from app.schemas.schemas import ModelMetrics, ModelVersionResponse, RetrainRequest, RetrainStatus
from app.services import ml_service
from app.api.auth import get_current_user, require_role
from app.models.database import User

router = APIRouter(prefix="/api/model", tags=["Model Management"])
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
METADATA_PATH = BASE_DIR / "backend" / "models_store" / "model_metadata.json"
COMPARISON_PATH = BASE_DIR / "backend" / "models_store" / "model_comparison.json"

_retrain_status: dict = {"status": "idle", "message": "No retraining in progress"}


@router.get("/metrics")
def get_model_metrics(current_user: User = Depends(get_current_user)):
    """
    Returns current production model metrics from held-out test set.
    Values are NEVER hardcoded — loaded dynamically from model_metadata.json.
    """
    if not METADATA_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Please run the training pipeline.",
        )
    with open(METADATA_PATH) as f:
        meta = json.load(f)
    return {
        "model_name": meta["model_name"],
        "model_version": meta["model_version"],
        "training_date": meta["training_date"],
        "dataset_size": meta["dataset_size"],
        "training_size": meta["training_size"],
        "testing_size": meta["testing_size"],
        "feature_count": meta["feature_count"],
        "accuracy": meta["accuracy"],
        "precision": meta["precision"],
        "recall": meta["recall"],
        "f2_score": meta["f2_score"],
        "roc_auc": meta["roc_auc"],
        "confusion_matrix": meta["confusion_matrix"],
        "is_production": True,
        "label": "Production Model — Test Set Performance",
    }


@router.get("/comparison")
def get_model_comparison(current_user: User = Depends(get_current_user)):
    """Returns comparison of all trained models from most recent training run."""
    if not COMPARISON_PATH.exists():
        raise HTTPException(status_code=503, detail="No comparison data. Please train the model first.")
    with open(COMPARISON_PATH) as f:
        comparison = json.load(f)

    # Mark which model is currently in production
    if METADATA_PATH.exists():
        with open(METADATA_PATH) as f:
            meta = json.load(f)
        prod_name = meta.get("model_name", "")
        for row in comparison:
            row["is_selected"] = (row.get("model_name", "") == prod_name)
    return {"comparison": comparison, "selection_rule": "Primary=F1 Score; Tiebreaker=F2 Score (recall-weighted)"}


@router.get("/history", response_model=list[ModelVersionResponse])
def get_model_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns all model versions stored in the database."""
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    result = []
    for v in versions:
        result.append(ModelVersionResponse(
            id=v.id,
            version=v.version,
            model_name=v.model_name,
            training_date=v.training_date,
            dataset_size=v.dataset_size,
            training_size=v.training_size,
            testing_size=v.testing_size,
            feature_count=v.feature_count,
            accuracy=v.accuracy,
            precision_score=v.precision_score,
            recall_score=v.recall_score,
            f2_score=v.f2_score,
            roc_auc=v.roc_auc,
            confusion_matrix=v.get_confusion_matrix(),
            model_comparison=v.get_model_comparison(),
            is_production=v.is_production,
            notes=v.notes or "",
            created_at=v.created_at,
        ))
    return result


@router.post("/retrain", response_model=RetrainStatus)
def retrain_model(
    request: RetrainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Trigger model retraining in background.
    Only accessible by Admin role.
    """
    global _retrain_status
    if _retrain_status.get("status") == "running":
        raise HTTPException(status_code=409, detail="Retraining is already in progress")

    _retrain_status = {"status": "running", "message": "Retraining started..."}
    background_tasks.add_task(_run_training, db, request.notes, current_user.id)
    return RetrainStatus(status="running", message="Training pipeline started in background")


@router.get("/retrain/status", response_model=RetrainStatus)
def get_retrain_status(current_user: User = Depends(get_current_user)):
    return RetrainStatus(**_retrain_status)


def _run_training(db: Session, notes: str, user_id: int):
    """Background training task."""
    global _retrain_status
    try:
        _retrain_status = {"status": "running", "message": "Training models...", "progress": 10}
        train_script = BASE_DIR / "backend" / "ml" / "train.py"
        result = subprocess.run(
            [sys.executable, str(train_script)],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR / "backend"),
        )
        if result.returncode != 0:
            _retrain_status = {
                "status": "failed",
                "message": f"Training failed: {result.stderr[-500:]}",
            }
            return

        # Reload model in service
        ml_service.reload_model()

        # Save version to DB
        if METADATA_PATH.exists():
            with open(METADATA_PATH) as f:
                meta = json.load(f)
            comparison = []
            if COMPARISON_PATH.exists():
                with open(COMPARISON_PATH) as f:
                    comparison = json.load(f)

            # Mark previous versions as non-production
            db.query(ModelVersion).update({"is_production": False})

            version = ModelVersion(
                version=meta["model_version"],
                model_name=meta["model_name"],
                training_date=datetime.fromisoformat(meta["training_date"]),
                dataset_size=meta["dataset_size"],
                training_size=meta["training_size"],
                testing_size=meta["testing_size"],
                feature_count=meta["feature_count"],
                accuracy=meta["accuracy"],
                precision_score=meta["precision"],
                recall_score=meta["recall"],
                f2_score=meta["f2_score"],
                roc_auc=meta["roc_auc"],
                confusion_matrix=json.dumps(meta["confusion_matrix"]),
                model_comparison=json.dumps(comparison),
                is_production=True,
                notes=notes,
            )
            db.add(version)
            db.commit()

        _retrain_status = {
            "status": "completed",
            "message": "Model retrained and deployed successfully",
            "progress": 100,
            "model_version": meta.get("model_version"),
            "metrics": {
                "accuracy": meta.get("accuracy"),
                "f2_score": meta.get("f2_score"),
            },
        }
    except Exception as e:
        logger.error(f"Training background task failed: {e}", exc_info=True)
        _retrain_status = {"status": "failed", "message": str(e)}
