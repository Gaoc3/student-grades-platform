from __future__ import annotations

import base64
import binascii
import re
import smtplib
import ssl
import textwrap
import time
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path

from email_validator import EmailNotValidError, validate_email

from app.core.config import settings


def normalize_email_address(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("Email address is required")

    try:
        return validate_email(cleaned, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


def _clean_text(value: str | None, fallback: str) -> str:
    cleaned = " ".join((value or "").split()).strip()
    return cleaned or fallback


def _sanitize_filename(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return slug.strip("._-") or "student"


def _build_grade_email_text(student_name: str, subject_name: str, grade_url: str, support_email: str) -> str:
    return textwrap.dedent(
        f"""
        Hi {student_name},

        Your grade access page for {subject_name} is ready.

        Open it here:
        {grade_url}

        This QR/link expires in {settings.qr_expiry_days} days.

        Need help? Contact {support_email}.
        """
    ).strip()


def _build_grade_email_html(
    *,
    brand_name: str,
    support_email: str,
    student_name: str,
    subject_name: str,
    grade_url: str,
    qr_base64: str,
) -> str:
    preheader = f"Your grade access page for {subject_name} is ready. Open the link or scan the QR code below."
    safe_brand = escape(brand_name)
    safe_support_email = escape(support_email)
    safe_student_name = escape(student_name)
    safe_subject_name = escape(subject_name)
    safe_grade_url = escape(grade_url, quote=True)

    return textwrap.dedent(
        f"""
        <!DOCTYPE html>
        <html lang="en">
          <body style="margin:0; padding:0; background:#eef4fb; color:#0f172a; font-family: Arial, 'Segoe UI', Tahoma, sans-serif;" dir="auto">
            <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent; line-height:1px; mso-hide:all;">
              {escape(preheader)}
            </div>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="width:100%; background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%); padding: 32px 16px;">
              <tr>
                <td align="center">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 680px; width:100%; background:#ffffff; border-radius: 28px; overflow:hidden; border: 1px solid #dbe7f6; box-shadow: 0 24px 60px -24px rgba(15, 23, 42, 0.35);">
                    <tr>
                      <td style="padding: 28px 30px; background: linear-gradient(135deg, #2563eb 0%, #0f766e 100%); color:#ffffff;">
                        <div style="font-size: 12px; font-weight: 800; letter-spacing: 0.24em; text-transform: uppercase; opacity: 0.9;">{safe_brand}</div>
                        <h1 style="margin: 12px 0 8px; font-size: 28px; line-height: 1.2; font-weight: 800;">Grade Access Ready</h1>
                        <p style="margin:0; font-size: 15px; line-height: 1.7; max-width: 560px; color: rgba(255,255,255,0.92);">Your lecturer published a secure grade page for <strong>{safe_subject_name}</strong>.</p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding: 30px 30px 12px;">
                        <p style="margin:0 0 10px; font-size: 16px; line-height:1.75; color:#0f172a;">Hi {safe_student_name},</p>
                        <p style="margin:0; font-size: 14px; line-height:1.8; color:#475569;">Scan the QR code below or use the secure button to open your published grades. If images are blocked in your mail client, the link still works.</p>
                      </td>
                    </tr>
                    <tr>
                      <td align="center" style="padding: 26px 30px 20px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 auto;">
                          <tr>
                            <td style="padding: 18px; border-radius: 24px; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); border: 1px solid #dbe7f6; box-shadow: 0 18px 38px -24px rgba(37, 99, 235, 0.55);">
                              <div style="font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color:#64748b; margin-bottom: 14px; text-align:center;">Scan the QR</div>
                              <div style="background:#ffffff; border-radius: 20px; padding: 16px; border: 1px solid #e5eef8; box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);">
                                <img src="cid:grade_qr" alt="QR code to open the grade page" width="248" style="display:block; width:248px; max-width:100%; height:auto; margin:0 auto; border-radius: 16px;" />
                              </div>
                              <div style="margin-top: 14px; font-size: 13px; line-height: 1.7; color:#475569; text-align:center;">This QR/link expires in <strong>{settings.qr_expiry_days} days</strong>.</div>
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                    <tr>
                      <td align="center" style="padding: 0 30px 18px;">
                        <a href="{safe_grade_url}" style="display:inline-block; padding: 15px 26px; border-radius: 16px; color:#ffffff; text-decoration:none; font-weight: 800; font-size: 15px; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); box-shadow: 0 14px 28px -12px rgba(37, 99, 235, 0.55);">Open Grade Page</a>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding: 0 30px 28px;">
                        <p style="margin:0; font-size: 13px; line-height:1.8; color:#64748b; text-align:center;">If the button does not open automatically, copy and paste this link:<br /><a href="{safe_grade_url}" style="color:#2563eb; word-break: break-all; text-decoration:none; font-weight:700;">{safe_grade_url}</a></p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding: 16px 30px 22px; background:#f8fbff; border-top: 1px solid #e5eef8; color:#64748b; font-size: 12px; line-height:1.7;">
                        Need help? Contact <a href="mailto:{safe_support_email}" style="color:#2563eb; text-decoration:none; font-weight:700;">{safe_support_email}</a>.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """
    ).strip()


def send_grade_qr_email(
    *,
    to_email: str,
    student_name: str,
    subject_name: str,
    grade_url: str,
    qr_base64: str,
    brand_name: str | None = None,
    support_email: str | None = None,
) -> tuple[bool, str]:
    normalized_email = None
    try:
        normalized_email = normalize_email_address(to_email)
    except ValueError as exc:
        return False, f"Invalid email address: {exc}"

    try:
        qr_bytes = base64.b64decode(qr_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        return False, f"Invalid QR image payload: {exc}"

    clean_brand_name = _clean_text(brand_name, settings.app_name)
    clean_support_email = _clean_text(support_email, settings.smtp_from)
    clean_student_name = _clean_text(student_name, "Student")
    clean_subject_name = _clean_text(subject_name, "Grade Access")
    clean_grade_url = grade_url.strip()

    msg = EmailMessage()
    msg["Subject"] = f"{clean_brand_name} | Grade access ready - {clean_subject_name}"
    msg["From"] = formataddr((clean_brand_name, settings.smtp_from))
    msg["To"] = normalized_email
    msg["Reply-To"] = clean_support_email

    msg.set_content(_build_grade_email_text(clean_student_name, clean_subject_name, clean_grade_url, clean_support_email))
    html = _build_grade_email_html(
        brand_name=clean_brand_name,
        support_email=clean_support_email,
        student_name=clean_student_name,
        subject_name=clean_subject_name,
        grade_url=clean_grade_url,
        qr_base64=qr_base64,
    )
    msg.add_alternative(html, subtype="html")
    msg.get_payload()[1].add_related(qr_bytes, maintype="image", subtype="png", cid="grade_qr")

    if not settings.smtp_host:
        out_dir = Path("offline_inbox")
        out_dir.mkdir(exist_ok=True)

        local_html = html.replace("cid:grade_qr", f"data:image/png;base64,{qr_base64}")
        filename = f"{int(time.time())}_{_sanitize_filename(clean_student_name)}_qr.html"
        file_path = out_dir / filename
        file_path.write_text(local_html, encoding="utf-8")
        return True, f"Saved offline ({file_path})"

    smtp_timeout = getattr(settings, "smtp_timeout", 20)
    use_ssl = bool(getattr(settings, "smtp_use_ssl", False)) or settings.smtp_port == 465
    use_starttls = bool(getattr(settings, "smtp_use_starttls", True)) and not use_ssl
    context = ssl.create_default_context()

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=smtp_timeout, context=context) as smtp:
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password or "")
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=smtp_timeout) as smtp:
                smtp.ehlo()
                if use_starttls and smtp.has_extn("starttls"):
                    smtp.starttls(context=context)
                    smtp.ehlo()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password or "")
                smtp.send_message(msg)
        return True, "sent"
    except smtplib.SMTPRecipientsRefused as exc:
        refused = exc.recipients.get(normalized_email)
        if refused:
            code = refused[0] if len(refused) > 0 else ""
            response = refused[1] if len(refused) > 1 else "Recipient rejected"
            return False, f"Recipient rejected by SMTP server ({code}): {response}"
        return False, f"Recipient rejected by SMTP server: {exc}"
    except smtplib.SMTPAuthenticationError as exc:
        response = exc.smtp_error.decode("utf-8", errors="ignore") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
        return False, f"SMTP authentication failed ({exc.smtp_code}): {response}"
    except smtplib.SMTPException as exc:
        return False, f"SMTP error: {exc}"
    except (OSError, ssl.SSLError) as exc:
        return False, f"Connection error: {exc}"
