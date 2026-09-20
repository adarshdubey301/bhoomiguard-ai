"""
BhoomiGuard AI — ML Training Pipeline
============================================================
Integrates and enhances the provided training script.
Trains 5 models, evaluates with F1 + F2 (beta=2), selects best
by F1 Score (per design), saves production model + metadata.

Usage:
    cd backend
    python ml/train.py
"""

import warnings
warnings.filterwarnings("ignore")

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # project root
DATASET_PATH = BASE_DIR / "data" / "land_acquisition_delay_dataset_10000.csv"
MODELS_DIR = BASE_DIR / "backend" / "models_store"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTION_MODEL_PATH = MODELS_DIR / "production_model.joblib"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
COMPARISON_PATH = MODELS_DIR / "model_comparison.json"

# ── Feature columns ────────────────────────────────────────────────────
TARGET_COLUMN = "delay_status"
EXCLUDE_COLUMNS = ["project_id", "delay_status"]   # never used as features

CATEGORICAL_FEATURES = ["district", "current_stage"]

NUMERICAL_FEATURES = [
    "total_land_parcels",
    "acquired_land_parcels",
    "pending_land_parcels",
    "total_landowners",
    "compensation_pending",
    "legal_cases",
    "documents_pending",
    "approval_pending_days",
    "objections_count",
    "survey_completed_percent",
    "previous_delay_days",
    "land_pending_percent",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERICAL_FEATURES


def load_and_validate_dataset(path: Path) -> pd.DataFrame:
    """Load CSV, validate columns and data quality, return clean DataFrame."""
    logger.info("=" * 60)
    logger.info("LOADING DATASET")
    logger.info("=" * 60)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    logger.info(f"Loaded {len(df):,} rows × {len(df.columns)} columns")

    # ── Required columns ──────────────────────────────────────────────
    required = FEATURE_COLUMNS + [TARGET_COLUMN, "project_id"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    logger.info("✓ All required columns present")

    # ── Data quality report ───────────────────────────────────────────
    logger.info("\n--- DATA QUALITY REPORT ---")
    logger.info(f"Total rows          : {len(df):,}")
    logger.info(f"Total columns       : {len(df.columns)}")

    # Missing values
    missing_counts = df.isnull().sum()
    total_missing = missing_counts.sum()
    logger.info(f"Missing values      : {total_missing}")
    if total_missing > 0:
        logger.warning("Columns with missing values:")
        for col, cnt in missing_counts[missing_counts > 0].items():
            logger.warning(f"  {col}: {cnt}")

    # Duplicates
    dup_count = df.duplicated().sum()
    logger.info(f"Duplicate rows      : {dup_count}")
    if dup_count > 0:
        logger.info(f"Removing {dup_count} duplicate rows...")
        df = df.drop_duplicates()

    # ── Target column cleaning ────────────────────────────────────────
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(str).str.strip().str.lower()
    valid_targets = {"yes", "no"}
    invalid_mask = ~df[TARGET_COLUMN].isin(valid_targets)
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        logger.warning(f"Removing {invalid_count} rows with invalid target values")
        df = df[~invalid_mask]
    df[TARGET_COLUMN] = df[TARGET_COLUMN].map({"no": 0, "yes": 1}).astype(int)

    # ── Logical validation (log only, don't silently fix) ─────────────
    invalid_acq = (df["acquired_land_parcels"] > df["total_land_parcels"]).sum()
    invalid_pct = ((df["survey_completed_percent"] < 0) | (df["survey_completed_percent"] > 100)).sum()
    invalid_lpp = ((df["land_pending_percent"] < 0) | (df["land_pending_percent"] > 100)).sum()
    invalid_comp = (df["compensation_pending"] > df["total_landowners"]).sum()
    if invalid_acq > 0:
        logger.warning(f"⚠ {invalid_acq} rows: acquired > total land parcels")
    if invalid_pct > 0:
        logger.warning(f"⚠ {invalid_pct} rows: survey_completed_percent out of [0,100]")
    if invalid_lpp > 0:
        logger.warning(f"⚠ {invalid_lpp} rows: land_pending_percent out of [0,100]")
    if invalid_comp > 0:
        logger.warning(f"⚠ {invalid_comp} rows: compensation_pending > total_landowners")

    # Recalculate derived features
    df["pending_land_parcels"] = (df["total_land_parcels"] - df["acquired_land_parcels"]).clip(lower=0)
    df["land_pending_percent"] = np.where(
        df["total_land_parcels"] > 0,
        (df["pending_land_parcels"] / df["total_land_parcels"]) * 100,
        0,
    ).round(2)

    # ── Target distribution ───────────────────────────────────────────
    dist = df[TARGET_COLUMN].value_counts().sort_index()
    logger.info(f"\nTarget distribution:")
    logger.info(f"  No Delay (0): {dist.get(0, 0):,}")
    logger.info(f"  Delay    (1): {dist.get(1, 0):,}")
    logger.info(f"  Total       : {len(df):,}")

    # ── Districts and stages ──────────────────────────────────────────
    districts = sorted(df["district"].dropna().unique().tolist())
    stages = sorted(df["current_stage"].dropna().unique().tolist())
    logger.info(f"\nDistricts ({len(districts)}): {districts}")
    logger.info(f"Stages    ({len(stages)}): {stages}")

    return df


def build_preprocessor() -> ColumnTransformer:
    """Build a ColumnTransformer pipeline with imputation + scaling/encoding."""
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numerical", numeric_pipeline, NUMERICAL_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])


def get_models() -> dict:
    """Return dict of model_name → sklearn estimator."""
    return {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=10, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=None, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, learning_rate=0.1, max_depth=3, random_state=42),
        "SVC": SVC(probability=True, random_state=42),
    }


def evaluate_model(pipeline, X_test, y_test) -> dict:
    """Calculate all metrics including F2 Score."""
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "f2_score": float(fbeta_score(y_test, y_pred, beta=2, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }


def train_all_models(X_train, X_test, y_train, y_test, preprocessor) -> tuple[dict, list]:
    """Train all models, return (trained_models dict, results list)."""
    models = get_models()
    results = []
    trained_models = {}

    logger.info("\n" + "=" * 60)
    logger.info("MODEL TRAINING")
    logger.info("=" * 60)

    for name, clf in models.items():
        logger.info(f"\n--- Training: {name} ---")
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ])
        pipeline.fit(X_train, y_train)
        metrics = evaluate_model(pipeline, X_test, y_test)
        trained_models[name] = pipeline

        logger.info(f"  Accuracy  : {metrics['accuracy']*100:.2f}%")
        logger.info(f"  Precision : {metrics['precision']*100:.2f}%")
        logger.info(f"  Recall    : {metrics['recall']*100:.2f}%")
        logger.info(f"  F1 Score  : {metrics['f1_score']*100:.2f}%")
        logger.info(f"  F2 Score  : {metrics['f2_score']*100:.2f}%  ← recall-weighted")
        logger.info(f"  ROC-AUC   : {metrics['roc_auc']*100:.2f}%")

        results.append({"model_name": name, **metrics})

    return trained_models, results


def select_best_model(results: list) -> str:
    """
    Model selection rule:
    Primary metric: F1 Score (balances precision and recall)
    Tiebreaker: F2 Score (emphasises recall — important for early-warning systems)
    Secondary: ROC-AUC
    This is an early-warning system, so missing delayed projects is costly.
    """
    sorted_results = sorted(results, key=lambda r: (r["f1_score"], r["f2_score"], r["roc_auc"]), reverse=True)
    best = sorted_results[0]
    logger.info("\n" + "=" * 60)
    logger.info("MODEL SELECTION")
    logger.info("=" * 60)
    logger.info(f"Selection rule: Primary=F1 Score, Tiebreaker=F2 Score (recall-weighted)")
    logger.info(f"Best model: {best['model_name']}")
    logger.info(f"  Accuracy  : {best['accuracy']*100:.2f}%")
    logger.info(f"  Precision : {best['precision']*100:.2f}%")
    logger.info(f"  Recall    : {best['recall']*100:.2f}%")
    logger.info(f"  F1 Score  : {best['f1_score']*100:.2f}%")
    logger.info(f"  F2 Score  : {best['f2_score']*100:.2f}%")
    logger.info(f"  ROC-AUC   : {best['roc_auc']*100:.2f}%")
    return best["model_name"]


def get_next_version() -> str:
    """Determine next model version by reading existing metadata."""
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH) as f:
                meta = json.load(f)
            current = meta.get("model_version", "v1.0")
            parts = current.lstrip("v").split(".")
            major, minor = int(parts[0]), int(parts[1])
            return f"v{major}.{minor + 1}"
        except Exception:
            pass
    return "v1.0"


def save_artifacts(best_pipeline, best_name: str, results: list, df: pd.DataFrame,
                   train_size: int, test_size: int) -> str:
    """Save model, metadata, and comparison JSON."""
    version = get_next_version()

    # Save model
    joblib.dump(best_pipeline, PRODUCTION_MODEL_PATH)
    logger.info(f"\n✓ Model saved → {PRODUCTION_MODEL_PATH}")

    # Find best model metrics
    best_metrics = next(r for r in results if r["model_name"] == best_name)
    cm = best_metrics["confusion_matrix"]

    # Metadata
    metadata = {
        "model_name": best_name,
        "model_version": version,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_size": len(df),
        "training_size": train_size,
        "testing_size": test_size,
        "feature_count": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "accuracy": best_metrics["accuracy"],
        "precision": best_metrics["precision"],
        "recall": best_metrics["recall"],
        "f1_score": best_metrics["f1_score"],
        "f2_score": best_metrics["f2_score"],
        "roc_auc": best_metrics["roc_auc"],
        "confusion_matrix": {
            "TN": cm[0][0], "FP": cm[0][1],
            "FN": cm[1][0], "TP": cm[1][1],
        },
        "districts": sorted(df["district"].dropna().unique().tolist()),
        "stages": sorted(df["current_stage"].dropna().unique().tolist()),
        "selection_rule": "Primary=F1 Score; Tiebreaker=F2 Score (recall-weighted); Secondary=ROC-AUC",
        "is_production": True,
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✓ Metadata saved → {METADATA_PATH}")

    # Comparison
    with open(COMPARISON_PATH, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"✓ Comparison saved → {COMPARISON_PATH}")

    return version


def print_comparison_table(results: list):
    logger.info("\n" + "=" * 60)
    logger.info("MODEL COMPARISON TABLE")
    logger.info("=" * 60)
    header = f"{'Model':<25} {'Acc':>7} {'Prec':>7} {'Rec':>7} {'F1':>7} {'F2':>7} {'AUC':>7}"
    logger.info(header)
    logger.info("-" * 75)
    for r in sorted(results, key=lambda x: x["f1_score"], reverse=True):
        row = (
            f"{r['model_name']:<25} "
            f"{r['accuracy']*100:>6.2f}% "
            f"{r['precision']*100:>6.2f}% "
            f"{r['recall']*100:>6.2f}% "
            f"{r['f1_score']*100:>6.2f}% "
            f"{r['f2_score']*100:>6.2f}% "
            f"{r['roc_auc']*100:>6.2f}%"
        )
        logger.info(row)


def test_prediction(pipeline, df: pd.DataFrame):
    """Demonstrate a sample prediction (no hardcoded values)."""
    logger.info("\n" + "=" * 60)
    logger.info("SAMPLE PREDICTION TEST")
    logger.info("=" * 60)

    # Use first row of dataset as example (excluding target)
    sample = df[FEATURE_COLUMNS].iloc[[0]].copy()
    pred = pipeline.predict(sample)[0]
    prob = pipeline.predict_proba(sample)[0][1]
    label = "⚠ DELAY EXPECTED" if pred == 1 else "✅ NO DELAY EXPECTED"
    logger.info(f"Sample district : {sample['district'].iloc[0]}")
    logger.info(f"Sample stage    : {sample['current_stage'].iloc[0]}")
    logger.info(f"Prediction      : {label}")
    logger.info(f"Probability     : {prob*100:.2f}%")


def main():
    logger.info("\n" + "=" * 60)
    logger.info("BHOOMIGUARD AI — ML TRAINING PIPELINE")
    logger.info("=" * 60)

    # 1. Load + validate
    df = load_and_validate_dataset(DATASET_PATH)

    # 2. Features / target
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    logger.info(f"\nFeatures ({len(FEATURE_COLUMNS)}): {FEATURE_COLUMNS}")
    logger.info(f"Target: {TARGET_COLUMN}  ← EXCLUDED from features ✓")

    # 3. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info(f"\nTrain size: {len(X_train):,}  |  Test size: {len(X_test):,}")

    # 4. Preprocessor
    preprocessor = build_preprocessor()

    # 5. Train all models
    trained_models, results = train_all_models(X_train, X_test, y_train, y_test, preprocessor)

    # 6. Print comparison
    print_comparison_table(results)

    # 7. Select best model
    best_name = select_best_model(results)
    best_pipeline = trained_models[best_name]

    # 8. Classification report for best model
    y_pred = best_pipeline.predict(X_test)
    logger.info("\n" + "=" * 60)
    logger.info("CLASSIFICATION REPORT — Best Model")
    logger.info("=" * 60)
    print(classification_report(y_test, y_pred, target_names=["No Delay", "Delay"], digits=4))

    # 9. Save artifacts
    version = save_artifacts(best_pipeline, best_name, results, df, len(X_train), len(X_test))

    # 10. Sample prediction
    test_prediction(best_pipeline, df)

    # 11. Summary
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Production model : {best_name}  {version}")
    logger.info(f"Model artifact   : {PRODUCTION_MODEL_PATH}")
    logger.info(f"Metadata         : {METADATA_PATH}")
    logger.info(f"Comparison       : {COMPARISON_PATH}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
