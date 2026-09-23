"""CSRF protection untuk form CTW."""
import secrets
from fastapi import Request, HTTPException, Form


def get_csrf_token(request: Request) -> str:
    """Ambil atau generate token CSRF dari session."""
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_urlsafe(32)
    return request.session["csrf_token"]


def verify_csrf(request: Request, csrf_token: str = Form("")) -> None:
    """Dependency untuk verifikasi token CSRF di POST request."""
    expected = request.session.get("csrf_token")
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="Session CSRF tidak ditemukan. Refresh halaman dan coba lagi.",
        )
    if not csrf_token or not secrets.compare_digest(csrf_token, expected):
        raise HTTPException(
            status_code=403,
            detail="CSRF token tidak valid. Refresh halaman dan coba lagi.",
        )
