from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.config import settings
from app.core.database import MainSessionLocal, tenant_session
from app.models import Doctor, Notification, PublicationToken


def cleanup_expired_tokens_and_notifications() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    notification_threshold = now - timedelta(days=settings.notification_retention_days)

    with MainSessionLocal() as main_db:
        doctor_ids = [d.id for d in main_db.scalars(select(Doctor)).all()]

    for doctor_id in doctor_ids:
        with tenant_session(doctor_id) as db:
            db.execute(delete(PublicationToken).where(PublicationToken.expires_at < now))
            db.execute(delete(Notification).where(Notification.created_at < notification_threshold))
            db.commit()
