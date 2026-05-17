"""
Database models
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Brute-force protection
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    # 2FA
    otp_secret = db.Column(db.String(64), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    two_fa_verified = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    login_logs = db.relationship("LoginLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def is_locked(self):
        """Return True if the account is currently locked out."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def lockout_remaining_seconds(self):
        """Seconds remaining in lockout (0 if not locked)."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            delta = self.locked_until - datetime.utcnow()
            return int(delta.total_seconds())
        return 0

    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None

    def __repr__(self):
        return f"<User {self.username}>"


class LoginLog(db.Model):
    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username_attempted = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    event_type = db.Column(db.String(32), nullable=False)   # SUCCESS, FAILED, LOCKED, OTP_SENT, OTP_SUCCESS, OTP_FAILED, LOGOUT, REGISTER
    details = db.Column(db.String(256), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<LoginLog {self.event_type} {self.username_attempted} @ {self.timestamp}>"
