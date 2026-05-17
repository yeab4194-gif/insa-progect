"""
Run once to create the admin user.
Usage:  python seed_admin.py
"""

from app import create_app
from extensions import db
from models import User
from utils.password import hash_password
from config import Config

app = create_app()

with app.app_context():
    existing = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
    if existing:
        print(f"Admin user '{Config.ADMIN_USERNAME}' already exists.")
    else:
        admin = User(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            password_hash=hash_password(Config.ADMIN_PASSWORD),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created:")
        print(f"  Username : {Config.ADMIN_USERNAME}")
        print(f"  Email    : {Config.ADMIN_EMAIL}")
        print(f"  Password : {Config.ADMIN_PASSWORD}")
        print("Change the password after first login!")
