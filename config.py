"""Konfigurasi environment CTW."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

ENV = os.getenv("CTW_ENV", "development").lower()
IS_DEV = ENV == "development"
IS_PROD = ENV == "production"

ENABLE_DOCS = os.getenv("CTW_ENABLE_DOCS", "true" if not IS_PROD else "false").lower() == "true"

SESSION_SECRET = os.getenv("CTW_SESSION_SECRET", "")

DB_PATH = ROOT / "data" / "processed" / "ctw.db"
DATABASE_URL = os.getenv("CTW_DATABASE_URL", f"sqlite:///{DB_PATH}")

UPLOAD_DIR = ROOT / "data" / "uploads"
PHOTO_DIR = UPLOAD_DIR / "photos"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# Batasan upload
MAX_PHOTO_SIZE_MB = 10
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
