from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_main_db, tenant_session
from app.core.security import decode_access_token
from app.models import Doctor


def get_current_doctor(request: Request, db: Session = Depends(get_main_db)) -> Doctor:
    token = request.cookies.get(settings.cookie_name)

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    doctor = db.get(Doctor, int(subject))
    if not doctor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found")
    return doctor


def get_tenant_db(current_doctor: Doctor = Depends(get_current_doctor)):
    with tenant_session(current_doctor.id) as db:
        yield db
