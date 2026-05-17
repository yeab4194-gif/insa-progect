"""
Application configuration
"""

import os
from datetime import timedelta


class Config:
    # Secret key for sessions and CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-use-a-long-random-string")

    # Database — SQLite for simplicity; swap URI for PostgreSQL/MySQL in production
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'auth_system.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session lifetime
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Brute-force protection
    MAX_LOGIN_ATTEMPTS = 5          # failed attempts before lockout
    LOCKOUT_DURATION_MINUTES = 15   # lockout duration

    # OTP settings
    OTP_EXPIRY_MINUTES = 10         # OTP valid for 10 minutes
    OTP_LENGTH = 6                  # 6-digit OTP

    # Email (Flask-Mail) — configure with real SMTP credentials
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")   # set in environment
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")   # set in environment
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@authsystem.local")

    # Admin credentials (first-run bootstrap)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@authsystem.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@1234!")
