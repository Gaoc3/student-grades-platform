from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import load_university_config, settings
from app.core.database import get_main_db, init_tenant_db, tenant_session
from app.core.dependencies import get_current_doctor
from app.core.security import clear_auth_cookie, create_access_token, decode_access_token, hash_password, set_auth_cookie, verify_password
from app.models import Doctor
from app.schemas import DoctorLogin, DoctorSignup
from app.services.grade_service import ensure_default_components

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def _resolve_authenticated_doctor(request: Request, db: Session) -> Doctor | None:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    subject = payload.get("sub")
    if not subject:
        return None

    try:
        doctor_id = int(subject)
    except (TypeError, ValueError):
        return None

    return db.get(Doctor, doctor_id)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_main_db)):
    doctor = _resolve_authenticated_doctor(request, db)
    return RedirectResponse(url="/dashboard" if doctor else "/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_main_db)):
    doctor = _resolve_authenticated_doctor(request, db)
    if doctor:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        request,
        "login.html",
        {"university": load_university_config()},
    )


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request, db: Session = Depends(get_main_db)):
    doctor = _resolve_authenticated_doctor(request, db)
    if doctor:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        request,
        "signup.html",
        {"university": load_university_config()},
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, doctor: Doctor = Depends(get_current_doctor)):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "doctor": doctor,
            "university": load_university_config(),
        },
    )


@router.post("/api/auth/signup")
def signup(payload: DoctorSignup, response: Response, db: Session = Depends(get_main_db)):
    email = payload.email.lower().strip()
    exists = db.scalar(select(Doctor).where(Doctor.email == email))
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")

    doctor = Doctor(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        subject_name=payload.subject_name.strip(),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    init_tenant_db(doctor.id)
    with tenant_session(doctor.id) as tenant_db:
        ensure_default_components(tenant_db)

    expires = timedelta(days=settings.remember_days)
    token = create_access_token(subject=str(doctor.id), expires_delta=expires)
    set_auth_cookie(response, token, int(expires.total_seconds()))

    return {
        "message": "Account created",
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "subject_name": doctor.subject_name,
        },
    }


@router.post("/api/auth/login")
def login(payload: DoctorLogin, response: Response, db: Session = Depends(get_main_db)):
    doctor = db.scalar(select(Doctor).where(Doctor.email == payload.email.lower().strip()))
    if not doctor or not verify_password(payload.password, doctor.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    expires = (
        timedelta(days=settings.remember_days)
        if payload.remember_me
        else timedelta(hours=settings.token_expire_hours)
    )
    token = create_access_token(subject=str(doctor.id), expires_delta=expires)
    set_auth_cookie(response, token, int(expires.total_seconds()))

    return {
        "message": "Logged in",
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "subject_name": doctor.subject_name,
        },
    }


@router.post("/api/auth/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out"}


@router.get("/api/auth/me")
def me(doctor: Doctor = Depends(get_current_doctor)):
    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "email": doctor.email,
        "subject_name": doctor.subject_name,
    }
