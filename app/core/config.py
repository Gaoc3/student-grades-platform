from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Student Grades Platform"
    secret_key: str = "please-change-this-secret-key"
    algorithm: str = "HS256"

    main_db_url: str = "sqlite:///./data/main.db"
    tenant_dir: str = "./data/tenants"

    cookie_name: str = "sgp_session"
    cookie_secure: bool = False
    token_expire_hours: int = 8
    remember_days: int = 14

    qr_expiry_days: int = 3
    notification_retention_days: int = 30

    public_base_url: str = "http://127.0.0.1:8000"
    default_rate_limit: str = "120/minute"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@university.edu"


settings = Settings()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def university_config_path() -> Path:
    return project_root() / "config" / "university.json"


def load_university_config() -> dict[str, Any]:
    default = {
        "university_name": "University Name Here",
        "university_logo_path": "/static/images/university-logo.png",
        "college_name": "College Name Here",
        "support_email": "support@university.edu",
    }

    cfg_path = university_config_path()
    if not cfg_path.exists():
        return default

    try:
        payload = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return default

    return {**default, **payload}
