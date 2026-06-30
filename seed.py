"""
Seed script — creates all tables and inserts the default superadmin.
Run: python database/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.connection import engine, SessionLocal
from database.models import Base, User
from services.auth_service import hash_password


def seed():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] Tables created.")

    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "superadmin@gmail.com")
        existing = db.query(User).filter(User.email == admin_email).first()
        if existing:
            existing.password_hash = hash_password(os.getenv("ADMIN_PASSWORD", "admin123"))
            existing.role = "admin"
            db.commit()
            print(f"[SUCCESS] Admin '{admin_email}' credentials updated/verified.")
            return

        admin = User(
            email=admin_email,
            full_name=os.getenv("ADMIN_NAME", "Super Admin"),
            password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "admin123")),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print(f"[SUCCESS] Superadmin seeded: {admin_email} / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
