"""
Security event logging helpers
"""

from flask import request
from extensions import db
from models import LoginLog


def log_event(event_type: str, username: str, user_id: int = None, details: str = None):
    """
    Persist a security event to the login_logs table.

    event_type values: SUCCESS, FAILED, LOCKED, OTP_SENT, OTP_SUCCESS,
                       OTP_FAILED, LOGOUT, REGISTER
    """
    ip = request.remote_addr or "unknown"
    ua = (request.user_agent.string or "")[:256]

    entry = LoginLog(
        user_id=user_id,
        username_attempted=username[:64],
        ip_address=ip,
        user_agent=ua,
        event_type=event_type,
        details=(details or "")[:256],
    )
    db.session.add(entry)
    db.session.commit()
