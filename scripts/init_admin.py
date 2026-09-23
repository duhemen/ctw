"""Buat user admin default."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import SessionLocal, init_db
from core.models import User
from core.auth import hash_password


def main():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("User 'admin' sudah ada.")
            reset = input("Reset password ke 'admin123'? (y/N): ").strip().lower()
            if reset == "y":
                existing.hashed_password = hash_password("admin123")
                db.commit()
                print("[OK] Password admin direset.")
            return

        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            full_name="Administrator",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("[OK] User admin dibuat.")
        print("     Username: admin")
        print("     Password: admin123")
        print("     -> Ganti password setelah login pertama!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
