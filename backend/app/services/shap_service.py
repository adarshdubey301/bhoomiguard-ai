"""
BhoomiGuard AI — SHAP Explanation Service
Provides SHAP-based explanations for delay predictions.
"""
import logging
from typing import Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FEATURE_LABELS = {
    "total_land_parcels": "Total Land Parcels",
    "acquired_land_parcels": "Acquired Land Parcels",
    "pending_land_parcels": "Pending Land Parcels",
    "total_landowners": "Total Landowners",
    "compensation_pending": "Compensation Pending",
    "legal_cases": "Legal Cases",
    "documents_pending": "Documents Pending",
    "approval_pending_days": "Approval Pending Days",
    "objections_count": "Objections Count",
    "survey_completed_percent": "Survey Completed %",
    "current_stage": "Current Stage",
    "previous_delay_days": "Previous Delay Days",
    "land_pending_percent": "Land Pending %",
    "district": "District",
}


def get_shap_explanation(model_pipeline, df_input: pd.DataFrame, top_n: int = 7) -> list[dict]:
    """
    Compute SHAP values for a single prediction using the trained pipeline.
    Returns top_n risk factors sorted by absolute SHAP value.
    """
    try:
        import shap

        classifier = model_pipeline.named_steps["classifier"]
        preprocessor = model_pipeline.named_steps["preprocessor"]

        # Transform input
        X_transformed = preprocessor.transform(df_input)

        model_type = type(classifier).__name__
        explainer = None

        if model_type in ("RandomForestClassifier", "GradientBoostingClassifier",
                           "DecisionTreeClassifier", "XGBClassifier"):
            try:
                explainer = shap.TreeExplainer(classifier)
                shap_values = explainer.shap_values(X_transformed)
                # For binary classification, take class=1 values
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    vals = shap_values[1][0]
                elif hasattr(shap_values, 'shape') and len(shap_values.shape) == 3:
                    vals = shap_values[0, :, 1]
                else:
                    vals = shap_values[0] if shap_values.ndim > 1 else shap_values
            except Exception:
                explainer = None

        if explainer is None:
            try:
                explainer = shap.LinearExplainer(classifier, X_transformed)
                shap_values = explainer.shap_values(X_transformed)
                if isinstance(shap_values, list):
                    vals = shap_values[1][0] if len(shap_values) == 2 else shap_values[0][0]
                else:
                    vals = shap_values[0]
            except Exception:
                # Fallback: use feature importance if available
                return _fallback_importance(model_pipeline, df_input, top_n)

        # Get feature names from preprocessor
        feature_names = _get_feature_names(preprocessor, df_input)

        if len(vals) != len(feature_names):
            feature_names = [f"feature_{i}" for i in range(len(vals))]

        # Map transformed features back to original feature groups
        original_features = _aggregate_to_original(feature_names, vals, df_input)

        # Sort by absolute value
        original_features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        top_factors = original_features[:top_n]

        result = []
        for f in top_factors:
            result.append({
                "feature": FEATURE_LABELS.get(f["original_feature"], f["original_feature"]),
                "importance": round(abs(f["shap_value"]), 4),
                "direction": "increases_risk" if f["shap_value"] > 0 else "decreases_risk",
                "value": f["value"],
            })
        return result

    except Exception as e:
        logger.error(f"SHAP explanation failed: {e}")
        return _fallback_importance(model_pipeline, df_input, top_n)


def _get_feature_names(preprocessor, df_input: pd.DataFrame) -> list[str]:
    """Extract feature names from ColumnTransformer."""
    try:
        names = []
        for name, transformer, cols in preprocessor.transformers_:
            if name == "numerical":
                names.extend(cols)
            elif name == "categorical":
                ohe = transformer.named_steps.get("onehot")
                if ohe is not None and hasattr(ohe, "get_feature_names_out"):
                    names.extend(ohe.get_feature_names_out(cols).tolist())
                else:
                    names.extend(cols)
        return names
    except Exception:
        return []


def _aggregate_to_original(feature_names: list, shap_vals, df_input: pd.DataFrame) -> list[dict]:
    """Aggregate one-hot encoded features back to original categorical features."""
    aggregated = {}
    original_cols = list(df_input.columns)

    for fname, sv in zip(feature_names, shap_vals):
        # Check if it's a one-hot feature (e.g., "district_Ahmedabad")
        matched_original = None
        for col in original_cols:
            if fname.startswith(f"{col}_") or fname == col:
                matched_original = col
                break

        if matched_original is None:
            matched_original = fname

        if matched_original not in aggregated:
            val = df_input[matched_original].iloc[0] if matched_original in df_input.columns else fname
            if hasattr(val, "item"): val = val.item() # Cast numpy types to python native types
            aggregated[matched_original] = {"original_feature": matched_original, "shap_value": 0.0, "value": str(val)}
        aggregated[matched_original]["shap_value"] += float(sv)

    return list(aggregated.values())


def _fallback_importance(model_pipeline, df_input: pd.DataFrame, top_n: int) -> list[dict]:
    """Fallback when SHAP fails — use feature importances or coefficient magnitudes."""
    try:
        classifier = model_pipeline.named_steps["classifier"]
        preprocessor = model_pipeline.named_steps["preprocessor"]
        X_transformed = preprocessor.transform(df_input)
        feature_names = _get_feature_names(preprocessor, df_input)

        if hasattr(classifier, "feature_importances_"):
            importances = classifier.feature_importances_
        elif hasattr(classifier, "coef_"):
            importances = np.abs(classifier.coef_[0])
        else:
            importances = np.ones(X_transformed.shape[1])

        original = _aggregate_to_original(feature_names, importances, df_input)
        original.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        result = []
        for f in original[:top_n]:
            result.append({
                "feature": FEATURE_LABELS.get(f["original_feature"], f["original_feature"]),
                "importance": round(abs(f["shap_value"]), 4),
                "direction": "increases_risk",
                "value": f["value"],
            })
        return result
    except Exception as e:
        logger.error(f"Fallback importance failed: {e}")
        return []
