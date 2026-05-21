from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from email.message import EmailMessage

from app.core.config import settings


def send_grade_qr_email(*, to_email: str, student_name: str, subject_name: str, grade_url: str, qr_base64: str) -> tuple[bool, str]:
    msg = EmailMessage()
    msg["Subject"] = f"{subject_name} - Grade Access QR"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    html = f"""
    <html>
      <body style=\"font-family: Arial, sans-serif;\">
        <h2>Grade Access</h2>
        <p>Hi {student_name},</p>
        <p>Your lecturer published new grade data. Scan the QR below or open the direct link.</p>
        <p><a href=\"{grade_url}\">Open Grade Page</a></p>
        <p><img src=\"cid:grade_qr\" alt=\"QR code\" width=\"230\"/></p>
        <div style=\"background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 12px 16px; margin-top: 16px; color: #856404;\">
          ⏳ <strong>Important:</strong> This QR/link expires in <strong>{settings.qr_expiry_days} days</strong>. Please view your grades before the link expires.
        </div>
      </body>
    </html>
    """
    msg.set_content(f"Hi {student_name}, open your grade from: {grade_url} (expires in {settings.qr_expiry_days} days)")
    msg.add_alternative(html, subtype="html")

    qr_bytes = base64.b64decode(qr_base64)
    msg.get_payload()[1].add_related(qr_bytes, maintype="image", subtype="png", cid="grade_qr")

    if not settings.smtp_host:
        # Offline mode fallback: write email to local directory
        out_dir = Path("offline_inbox")
        out_dir.mkdir(exist_ok=True)
        
        # Replace cid with data URI so it renders locally in browser
        local_html = html.replace('cid:grade_qr', f'data:image/png;base64,{qr_base64}')
        
        filename = f"{int(time.time())}_{student_name.replace(' ', '_')}_qr.html"
        file_path = out_dir / filename
        file_path.write_text(local_html, encoding="utf-8")
        
        return True, f"Saved offline ({file_path})"

    try:
        import smtplib
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password or "")
            smtp.send_message(msg)
        return True, "sent"
    except Exception as exc:
        return False, str(exc)
