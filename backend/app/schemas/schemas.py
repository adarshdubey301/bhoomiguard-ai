"""
BhoomiGuard AI — Pydantic v2 Schemas
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────────
# Auth Schemas
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    role: str = Field(default="viewer", pattern="^(admin|officer|viewer)$")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Prediction Input Schema
# ─────────────────────────────────────────────

class PredictionInput(BaseModel):
    """
    Input features for the land acquisition delay prediction model.
    NOTE: delay_status is intentionally excluded — it is the TARGET variable.
    NOTE: project_id is intentionally excluded — it is an identifier, not a feature.
    """
    district: str = Field(..., description="District name")
    total_land_parcels: int = Field(..., ge=1, description="Total land parcels in project")
    acquired_land_parcels: int = Field(..., ge=0, description="Parcels already acquired")
    pending_land_parcels: int = Field(..., ge=0, description="Parcels pending acquisition")
    total_landowners: int = Field(..., ge=1, description="Total number of landowners")
    compensation_pending: int = Field(..., ge=0, description="Landowners with pending compensation")
    legal_cases: int = Field(..., ge=0, description="Active legal cases")
    documents_pending: int = Field(..., ge=0, description="Documents pending verification")
    approval_pending_days: int = Field(..., ge=0, description="Days with pending approval")
    objections_count: int = Field(..., ge=0, description="Number of objections filed")
    survey_completed_percent: float = Field(..., ge=0.0, le=100.0, description="Survey completion %")
    current_stage: str = Field(..., description="Current acquisition stage")
    previous_delay_days: int = Field(..., ge=0, description="Delay days in previous projects")
    land_pending_percent: float = Field(..., ge=0.0, le=100.0, description="Pending land percentage")

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.acquired_land_parcels > self.total_land_parcels:
            raise ValueError("acquired_land_parcels cannot exceed total_land_parcels")
        if self.pending_land_parcels > self.total_land_parcels:
            raise ValueError("pending_land_parcels cannot exceed total_land_parcels")
        if self.compensation_pending > self.total_landowners:
            raise ValueError("compensation_pending cannot exceed total_landowners")
        return self


class PredictionInputWithId(PredictionInput):
    project_id: Optional[str] = Field(None, description="Optional project identifier for tracking")


# ─────────────────────────────────────────────
# Prediction Response Schema
# ─────────────────────────────────────────────

class RiskFactor(BaseModel):
    feature: str
    importance: float
    direction: str  # "increases_risk" | "decreases_risk"
    value: Any


class Recommendation(BaseModel):
    priority: str  # "High" | "Medium" | "Low"
    action: str
    reason: str


class PredictionResponse(BaseModel):
    prediction: str                          # "Yes" | "No"
    delay_probability: float
    risk_level: str                          # Low | Medium | High | Critical
    district: str
    current_stage: str
    model_name: str
    model_version: str
    top_risk_factors: list[RiskFactor]
    recommendations: list[Recommendation]
    district_context: Optional[dict] = None
    unknown_district_warning: Optional[str] = None


class PredictionRecord(BaseModel):
    id: int
    project_id: str
    district: str
    current_stage: str
    prediction: str
    delay_probability: float
    risk_level: str
    model_name: str
    model_version: str
    top_risk_factors: list
    recommendations: list
    created_at: datetime
    created_by: Optional[int] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Model Schemas
# ─────────────────────────────────────────────

class ModelMetrics(BaseModel):
    model_name: str
    model_version: str
    training_date: str
    dataset_size: int
    training_size: int
    testing_size: int
    feature_count: int
    accuracy: float
    precision: float
    recall: float
    f2_score: float
    roc_auc: float
    confusion_matrix: dict
    is_production: bool = True


class ModelComparisonRow(BaseModel):
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    f2_score: float
    roc_auc: float
    is_selected: bool = False


class ModelVersionResponse(BaseModel):
    id: int
    version: str
    model_name: str
    training_date: datetime
    dataset_size: int
    training_size: int
    testing_size: int
    feature_count: int
    accuracy: float
    precision_score: float
    recall_score: float
    f2_score: float
    roc_auc: float
    confusion_matrix: dict
    model_comparison: list
    is_production: bool
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RetrainRequest(BaseModel):
    notes: str = ""
    force: bool = False


class RetrainStatus(BaseModel):
    status: str   # "running" | "completed" | "failed"
    message: str
    progress: Optional[int] = None    # 0-100
    model_version: Optional[str] = None
    metrics: Optional[dict] = None


# ─────────────────────────────────────────────
# Metadata Schema
# ─────────────────────────────────────────────

class MetadataResponse(BaseModel):
    districts: list[str]
    current_stages: list[str]
    risk_thresholds: dict
    total_records: int


# ─────────────────────────────────────────────
# Analytics Schemas
# ─────────────────────────────────────────────

class OverviewStats(BaseModel):
    total_projects: int
    delayed_projects: int
    non_delayed_projects: int
    delay_rate: float
    high_risk_predictions: int
    critical_predictions: int
    total_predictions: int
    district: Optional[str] = None
    stage: Optional[str] = None


class DistrictStats(BaseModel):
    district: str
    total_projects: int
    delayed_projects: int
    delay_rate: float
    avg_pending_land: float
    avg_approval_pending: float
    avg_legal_cases: float
    avg_compensation_pending: float
    high_risk_count: int
    critical_count: int
    rank: Optional[int] = None


class StageDistribution(BaseModel):
    stage: str
    count: int
    delayed: int
    delay_rate: float


class RiskDistribution(BaseModel):
    risk_level: str
    count: int
    percentage: float
