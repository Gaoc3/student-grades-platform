from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.core.config import settings
from app.models import MainBase, TenantBase


def is_postgresql() -> bool:
    return settings.main_db_url.startswith("postgres://") or settings.main_db_url.startswith("postgresql://")


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


if is_postgresql():
    main_engine: Engine = create_engine(
        settings.main_db_url,
        future=True,
    )
else:
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
    if is_postgresql():
        return main_engine

    if doctor_id in _tenant_engines:
        return _tenant_engines[doctor_id]

    db_path = tenant_db_path(doctor_id)
    url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    _tenant_engines[doctor_id] = engine
    return engine


def init_main_db() -> None:
    MainBase.metadata.create_all(bind=main_engine)
    if is_postgresql():
        TenantBase.metadata.create_all(bind=main_engine)


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
    if is_postgresql():
        db = MainSessionLocal()
        db.info["doctor_id"] = doctor_id
        try:
            yield db
        finally:
            db.close()
    else:
        engine = get_tenant_engine(doctor_id)
        # Keep tenant schema up-to-date for additive table changes.
        TenantBase.metadata.create_all(bind=engine)

        tenant_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        db = tenant_factory()
        try:
            yield db
        finally:
            db.close()


# Multi-tenancy event hooks for PostgreSQL
if is_postgresql():
    @event.listens_for(Session, "do_orm_execute")
    def _add_doctor_filter(orm_execute_state):
        doctor_id = orm_execute_state.session.info.get("doctor_id")
        if doctor_id is None:
            return

        if orm_execute_state.is_select:
            orm_execute_state.statement = orm_execute_state.statement.options(
                with_loader_criteria(
                    TenantBase,
                    lambda cls: cls.doctor_id == doctor_id,
                    include_aliases=True,
                    propagate_to_loaders=True,
                )
            )

    @event.listens_for(Session, "before_flush")
    def _assign_doctor_id(session, flush_context, instances):
        doctor_id = session.info.get("doctor_id")
        if doctor_id is None:
            return
        for obj in session.new:
            if isinstance(obj, TenantBase):
                if getattr(obj, "doctor_id", None) is None:
                    obj.doctor_id = doctor_id

