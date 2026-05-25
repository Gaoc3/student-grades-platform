from __future__ import annotations

import json
import ipaddress
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.core.config import load_university_config, settings
from app.core.dependencies import get_current_doctor, get_tenant_db
from app.core.database import tenant_session
from app.models import Doctor, GradeComponent, Notification, PublicationToken, Student, StudentScore
from app.schemas import PublishRequest
from app.services.email_service import send_grade_qr_email
from app.services.qr_service import create_token, make_qr_base64

router = APIRouter(tags=["publishing"])
templates = Jinja2Templates(directory="app/templates")


def _resolve_public_base_url(request: Request) -> str:
    configured_base_url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if configured_base_url and not _is_private_base_url(configured_base_url):
        return configured_base_url.rstrip("/")
    return str(request.base_url).rstrip("/")


def _is_private_base_url(base_url: str) -> bool:
    parsed = urlparse(base_url)
    hostname = parsed.hostname
    if not hostname:
        return False

    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True

    try:
        host_ip = ipaddress.ip_address(hostname)
    except ValueError:
        return False

    return host_ip.is_private or host_ip.is_loopback or host_ip.is_link_local


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/api/publish")
def publish_grades(
    request: Request,
    payload: PublishRequest,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_tenant_db),
) -> dict[str, object]:
    component_keys = payload.component_keys
    if not component_keys:
        raise HTTPException(status_code=400, detail="Select at least one grade component")

    target_components = db.scalars(
        select(GradeComponent).where(GradeComponent.semester == payload.semester)
    ).all()
    
    if not target_components:
        raise HTTPException(status_code=400, detail="No components defined for this semester.")

    target_component_map = {c.component_key: c for c in target_components}
    selected_component_keys = [key for key in component_keys if key in target_component_map]
    invalid_component_keys = sorted(set(component_keys) - set(selected_component_keys))

    if invalid_component_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Selected components do not belong to semester {payload.semester}: {', '.join(invalid_component_keys)}",
        )

    if not selected_component_keys:
        raise HTTPException(status_code=400, detail="No matching components for this semester")

    required_keys = set(selected_component_keys)

    student_stmt = select(Student)
    if payload.student_ids is not None:
        student_stmt = student_stmt.where(Student.id.in_(payload.student_ids))
    students = db.scalars(student_stmt).all()
    
    if not students:
        raise HTTPException(status_code=400, detail="No students selected.")

    # --- NEW: Check for completeness ---
    score_rows = db.scalars(
        select(StudentScore).where(
            StudentScore.student_id.in_([s.id for s in students]),
            StudentScore.component_key.in_(required_keys)
        )
    ).all()
    
    from collections import defaultdict
    student_scores_map: dict[int, set[str]] = defaultdict(set)
    for sr in score_rows:
        student_scores_map[sr.student_id].add(sr.component_key)
        
    for st in students:
        missing = required_keys - student_scores_map[st.id]
        if missing:
            missing_labels = [c.label for c in target_components if c.component_key in missing]
            raise HTTPException(
                status_code=400, 
                detail=f"لا يمكن الإذاعة: الطالب '{st.full_name}' تنقصه درجات في الكورس. (النواقص: {', '.join(missing_labels)})"
            )
    # -----------------------------------

    sent: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for st in students:
        rows = db.scalars(
            select(StudentScore).where(
                StudentScore.student_id == st.id,
                StudentScore.component_key.in_(selected_component_keys),
            )
        ).all()

        if not rows:
            continue

        for row in rows:
            row.published = True

        if not payload.send_email and not payload.force_new_token:
            continue

        if not st.email:
            skipped.append({"student": st.full_name, "reason": "No email"})
            continue

        active = db.scalar(
            select(PublicationToken).where(
                PublicationToken.student_id == st.id,
                PublicationToken.expires_at > now,
                PublicationToken.opened_at.is_(None),
            )
        )
        if active and not payload.force_new_token:
            skipped.append({"student": st.full_name, "reason": "Active unseen token already exists"})
            continue

        if payload.force_new_token:
            db.execute(
                delete(PublicationToken).where(PublicationToken.student_id == st.id)
            )

        token = create_token()
        expires_at = now + timedelta(days=settings.qr_expiry_days)
        token_row = PublicationToken(student_id=st.id, token=token, expires_at=expires_at)
        db.add(token_row)
        db.commit()

        base_url = _resolve_public_base_url(request)
        grade_url = f"{base_url}/grade/{token}"
        qr_base64 = make_qr_base64(grade_url)
        ok, detail = send_grade_qr_email(
            to_email=st.email,
            student_name=st.full_name,
            subject_name=doctor.subject_name,
            grade_url=grade_url,
            qr_base64=qr_base64,
        )

        sent.append({"student": st.full_name, "email": st.email, "status": "sent" if ok else "failed", "detail": detail, "grade_url": grade_url})

    db.commit()

    db.add(
        Notification(
            event_type="publish",
            message=f"Grades published for {len(students)} student(s) in {doctor.subject_name}",
            payload_json=json.dumps({
                "components": selected_component_keys,
                "student_count": len(students),
                "subject": doctor.subject_name
            }),
        )
    )
    db.commit()

    return {"message": "Publish completed", "emailed": sent, "skipped": skipped}


@router.get("/api/notifications")
def notifications(limit: int = 50, db: Session = Depends(get_tenant_db)) -> list[dict[str, object]]:
    rows = db.scalars(select(Notification).order_by(desc(Notification.created_at)).limit(max(1, min(limit, 200)))).all()
    return [
        {
            "id": n.id,
            "event_type": n.event_type,
            "message": n.message,
            "payload": n.payload_json,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in rows
    ]


@router.post("/api/notifications/cleanup")
def cleanup_notifications(db: Session = Depends(get_tenant_db)):
    db.execute(delete(Notification))
    db.commit()
    return {"message": "All notifications cleared"}


@router.delete("/api/notifications/{notif_id}")
def delete_notification(notif_id: int, db: Session = Depends(get_tenant_db)):
    row = db.get(Notification, notif_id)
    if row:
        db.delete(row)
        db.commit()
    return {"message": "Deleted"}


@router.get("/grade/{token}", response_class=HTMLResponse)
def grade_page(request: Request, token: str):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    found = None
    doctor_info = None

    from app.core.database import MainSessionLocal

    with MainSessionLocal() as main_db:
        doctors = main_db.scalars(select(Doctor)).all()
        for doctor in doctors:
            with tenant_session(doctor.id) as tenant_db:
                row = tenant_db.scalar(select(PublicationToken).where(PublicationToken.token == token))
                if row:
                    found = row
                    doctor_info = doctor
                    break

                # session closes, continue loop

            if found:
                break

    if not found or not doctor_info:
        return templates.TemplateResponse(
            request,
            "token_invalid.html",
            {"university": load_university_config(), "reason": "الرابط غير صالح"},
            status_code=404,
        )

    with tenant_session(doctor_info.id) as db:
        token_row = db.scalar(select(PublicationToken).where(PublicationToken.token == token))
        if not token_row:
            return templates.TemplateResponse(
                request,
                "token_invalid.html",
                {"university": load_university_config(), "reason": "الرابط غير صالح"},
                status_code=404,
            )

        expires_at = token_row.expires_at
        if not expires_at or expires_at < now:
            db.delete(token_row)
            db.commit()
            return templates.TemplateResponse(
                request,
                "token_invalid.html",
                {
                    "university": load_university_config(),
                    "reason": "انتهت صلاحية QR، تواصل مع الدكتور لإرسال QR جديد",
                },
                status_code=410,
            )

        student = db.get(Student, token_row.student_id)
        if not student:
            return templates.TemplateResponse(
                request,
                "token_invalid.html",
                {"university": load_university_config(), "reason": "الطالب غير موجود"},
                status_code=404,
            )

        if token_row.opened_at is None:
            token_row.opened_at = now
            token_row.first_seen_ip = request.client.host if request.client else None

        # Notify on every view
        db.add(
            Notification(
                event_type="grade_viewed",
                message=f"{student.full_name} فتح صفحة الدرجات",
                payload_json=json.dumps({
                    "student_id": student.id,
                    "email": student.email,
                    "student_name": student.full_name
                }),
            )
        )
        db.commit()

        components = {
            c.component_key: c
            for c in db.scalars(select(GradeComponent)).all()
        }
        rows = db.scalars(
            select(StudentScore).where(
                StudentScore.student_id == student.id,
                StudentScore.published.is_(True),
            )
        ).all()

        grade_rows: list[dict[str, object]] = []
        total = 0.0
        max_total = 0.0

        for row in rows:
            comp = components.get(row.component_key)
            if not comp:
                continue
            total += row.score
            max_total += comp.max_score
            grade_rows.append(
                {
                    "label": comp.label,
                    "score": round(row.score, 2),
                    "max_score": round(comp.max_score, 2),
                }
            )

        return templates.TemplateResponse(
            request,
            "student_grade.html",
            {
                "university": load_university_config(),
                "student": student,
                "subject": doctor_info.subject_name,
                "grade_rows": grade_rows,
                "total": round(total, 2),
                "max_total": round(max_total, 2),
                "expires_at": token_row.expires_at.isoformat(),
            },
        )
