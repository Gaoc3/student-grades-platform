from __future__ import annotations

import base64
import io
import secrets

import qrcode
from qrcode.constants import ERROR_CORRECT_H


def create_token() -> str:
    return secrets.token_urlsafe(32)


def make_qr_base64(url: str) -> str:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
