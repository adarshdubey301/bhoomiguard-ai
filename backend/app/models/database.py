"""
BhoomiGuard AI — SQLAlchemy ORM Models
"""
import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="viewer")  # admin, officer, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    predictions = relationship("Prediction", back_populates="user", foreign_keys="Prediction.created_by")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(50), nullable=False, index=True)
    district = Column(String(100), nullable=False)
    current_stage = Column(String(50), nullable=False)
    prediction = Column(String(10), nullable=False)       # "Yes" / "No"
    delay_probability = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)        # Low/Medium/High/Critical
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    top_risk_factors = Column(Text, default="[]")          # JSON list
    recommendations = Column(Text, default="[]")           # JSON list
    input_features = Column(Text, default="{}")            # JSON dict
    created_at = Column(DateTime, default=utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="predictions", foreign_keys=[created_by])

    def get_top_risk_factors(self):
        return json.loads(self.top_risk_factors or "[]")

    def get_recommendations(self):
        return json.loads(self.recommendations or "[]")

    def get_input_features(self):
        return json.loads(self.input_features or "{}")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False, unique=True)
    model_name = Column(String(100), nullable=False)
    training_date = Column(DateTime, default=utcnow)
    dataset_size = Column(Integer, nullable=False)
    training_size = Column(Integer, nullable=False)
    testing_size = Column(Integer, nullable=False)
    feature_count = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    precision_score = Column(Float, nullable=False)
    recall_score = Column(Float, nullable=False)
    f2_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    confusion_matrix = Column(Text, default="{}")          # JSON
    model_comparison = Column(Text, default="[]")          # JSON list of all models
    is_production = Column(Boolean, default=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    def get_confusion_matrix(self):
        return json.loads(self.confusion_matrix or "{}")

    def get_model_comparison(self):
        return json.loads(self.model_comparison or "[]")
