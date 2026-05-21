from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import MainBase, TenantBase


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


main_engine: Engine = create_engine(
    settings.main_db_url,
    connect_args=_sqlite_connect_args(settings.main_db_url),
    future=True,
)
MainSessionLocal = sessionmaker(bind=main_engine, autoflush=False, autocommit=False, expire_on_commit=False)

_tenant_engines: dict[int, Engine] = {}


def ensure_tenant_dir() -> Path:
    tenant_dir = Path(settings.tenant_dir)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir


def tenant_db_path(doctor_id: int) -> Path:
    return ensure_tenant_dir() / f"doctor_{doctor_id}.db"


def get_tenant_engine(doctor_id: int) -> Engine:
    if doctor_id in _tenant_engines:
        return _tenant_engines[doctor_id]

    db_path = tenant_db_path(doctor_id)
    url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    _tenant_engines[doctor_id] = engine
    return engine


def init_main_db() -> None:
    MainBase.metadata.create_all(bind=main_engine)


def init_tenant_db(doctor_id: int) -> None:
    engine = get_tenant_engine(doctor_id)
    TenantBase.metadata.create_all(bind=engine)


def get_main_db() -> Generator[Session, None, None]:
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def tenant_session(doctor_id: int) -> Generator[Session, None, None]:
    engine = get_tenant_engine(doctor_id)
    # Keep tenant schema up-to-date for additive table changes.
    TenantBase.metadata.create_all(bind=engine)

    tenant_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = tenant_factory()
    try:
        yield db
    finally:
        db.close()
