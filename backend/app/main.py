"""
BhoomiGuard AI — FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.db import init_db
from app.api import auth, predict, model, predictions, analytics, metadata
from app.models.database import User, ModelVersion
from app.core.security import get_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _create_default_users():
    """Create default admin/officer/viewer accounts on first run."""
    from app.database.db import SessionLocal
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            default_users = [
                User(username="admin", email="admin@bhoomiguard.gov.in",
                     hashed_password=get_password_hash("admin123"), role="admin", is_active=True),
                User(username="districtofficer", email="district@bhoomiguard.gov.in",
                     hashed_password=get_password_hash("district123"), role="district_officer", is_active=True),
                User(username="projectofficer", email="project@bhoomiguard.gov.in",
                     hashed_password=get_password_hash("project123"), role="project_officer", is_active=True),
            ]
            db.add_all(default_users)
            db.commit()
            logger.info("Default users created: admin/admin123, districtofficer/district123, projectofficer/project123")
    except Exception as e:
        logger.warning(f"Could not create default users: {e}")
    finally:
        db.close()


def _seed_model_version():
    """If model artifacts exist but no DB record, create the initial record."""
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    from app.database.db import SessionLocal

    metadata_path = Path(__file__).resolve().parent.parent / "models_store" / "model_metadata.json"
    comparison_path = Path(__file__).resolve().parent.parent / "models_store" / "model_comparison.json"

    if not metadata_path.exists():
        return

    db = SessionLocal()
    try:
        if db.query(ModelVersion).count() == 0:
            with open(metadata_path) as f:
                meta = json.load(f)
            comparison = []
            if comparison_path.exists():
                with open(comparison_path) as f:
                    comparison = json.load(f)

            version = ModelVersion(
                version=meta.get("model_version", "v1.0"),
                model_name=meta["model_name"],
                training_date=datetime.fromisoformat(meta["training_date"]) if "training_date" in meta else datetime.now(timezone.utc),
                dataset_size=meta["dataset_size"],
                training_size=meta["training_size"],
                testing_size=meta["testing_size"],
                feature_count=meta["feature_count"],
                accuracy=meta["accuracy"],
                precision_score=meta["precision"],
                recall_score=meta["recall"],
                f2_score=meta["f2_score"],
                roc_auc=meta["roc_auc"],
                confusion_matrix=json.dumps(meta.get("confusion_matrix", {})),
                model_comparison=json.dumps(comparison),
                is_production=True,
                notes="Initial model — seeded on startup",
            )
            db.add(version)
            db.commit()
            logger.info(f"Seeded model version {meta.get('model_version')} to DB")
    except Exception as e:
        logger.warning(f"Could not seed model version: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("=" * 50)
    logger.info("BhoomiGuard AI — Starting up")
    logger.info("=" * 50)
    init_db()
    _create_default_users()
    _seed_model_version()
    logger.info("Startup complete")
    yield
    logger.info("BhoomiGuard AI — Shutting down")


app = FastAPI(title="BhoomiGuard AI API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(model.router)
app.include_router(predictions.router)
app.include_router(analytics.router)
app.include_router(metadata.router)


@app.get("/")
def root():
    return {"message": "BhoomiGuard AI Backend is Running"}


@app.get("/health")
def health():
    from app.services.ml_service import is_model_ready
    return {
        "status": "ok",
        "service": "BhoomiGuard AI"
    }
