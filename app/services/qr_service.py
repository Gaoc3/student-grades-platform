from __future__ import annotations

import base64
import io
import secrets

import qrcode


def create_token() -> str:
    return secrets.token_urlsafe(32)


def make_qr_base64(url: str) -> str:
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
