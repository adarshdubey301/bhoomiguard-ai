"""
BhoomiGuard AI — Application Configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "BhoomiGuard AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "bhoomiguard-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "sqlite:///./bhoomiguard.db"

    # Paths
    DATA_DIR: str = "../data"
    MODELS_DIR: str = "./models_store"
    DATASET_FILENAME: str = "land_acquisition_delay_dataset_10000.csv"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # Risk Thresholds
    RISK_LOW_MAX: float = 0.25
    RISK_MEDIUM_MAX: float = 0.50
    RISK_HIGH_MAX: float = 0.75

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def dataset_path(self) -> Path:
        base = Path(__file__).resolve().parent.parent.parent
        return base / self.DATA_DIR.lstrip("./").lstrip("../") / self.DATASET_FILENAME if ".." in self.DATA_DIR else Path(self.DATA_DIR) / self.DATASET_FILENAME

    @property
    def models_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent / "backend" / self.MODELS_DIR.lstrip("./")


settings = Settings()


def get_risk_level(probability: float) -> str:
    """Convert delay probability to risk level using configurable thresholds."""
    if probability < settings.RISK_LOW_MAX:
        return "Low"
    elif probability < settings.RISK_MEDIUM_MAX:
        return "Medium"
    elif probability < settings.RISK_HIGH_MAX:
        return "High"
    else:
        return "Critical"
