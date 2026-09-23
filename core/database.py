"""Konfigurasi database SQLAlchemy untuk CTW."""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data" / "processed"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "ctw.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from core import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
