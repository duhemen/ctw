"""Autentikasi & session untuk admin CTW."""
import hashlib
import secrets
from typing import Optional
from fastapi import Request


PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Hash password pakai PBKDF2-SHA256. Format: salt_hex:hash_hex."""
    salt = secrets.token_bytes(16)
    hash_val = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex() + ":" + hash_val.hex()


def verify_password(password: str, stored: str) -> bool:
    """Verifikasi password terhadap hash tersimpan."""
    try:
        salt_hex, hash_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return secrets.compare_digest(expected.hex(), hash_hex)
    except Exception:
        return False


def login_user(request: Request, user_id: int, username: str):
    """Simpan session user di cookie."""
    request.session["user_id"] = user_id
    request.session["username"] = username


def logout_user(request: Request):
    """Hapus session."""
    request.session.clear()


def get_current_user(request: Request) -> Optional[dict]:
    """Ambil user dari session. Return None kalau tidak login."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return {
        "id": user_id,
        "username": request.session.get("username", ""),
    }
