"""
OTP (One-Time Password) generation and email delivery
"""

import secrets
import string
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Message
from extensions import mail


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(length))


def send_otp_email(user_email: str, username: str, otp: str) -> bool:
    """
    Send the OTP to the user's email address.
    Returns True on success, False on failure.
    """
    try:
        msg = Message(
            subject="Your One-Time Password (OTP)",
            recipients=[user_email],
        )
        msg.body = (
            f"Hello {username},\n\n"
            f"Your One-Time Password (OTP) for login is:\n\n"
            f"    {otp}\n\n"
            f"This code is valid for {current_app.config['OTP_EXPIRY_MINUTES']} minutes.\n"
            f"Do NOT share this code with anyone.\n\n"
            f"If you did not request this, please change your password immediately.\n\n"
            f"— Auth System Security Team"
        )
        msg.html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                    border:1px solid #e0e0e0;border-radius:8px;padding:32px;">
          <h2 style="color:#2d3748;">Two-Factor Authentication</h2>
          <p>Hello <strong>{username}</strong>,</p>
          <p>Your One-Time Password is:</p>
          <div style="font-size:36px;font-weight:bold;letter-spacing:8px;
                      text-align:center;padding:16px;background:#f7fafc;
                      border-radius:6px;color:#2b6cb0;">{otp}</div>
          <p style="margin-top:16px;color:#718096;font-size:13px;">
            Valid for <strong>{current_app.config['OTP_EXPIRY_MINUTES']} minutes</strong>.
            Do not share this code.
          </p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.error(f"Failed to send OTP email to {user_email}: {exc}")
        return False


def set_user_otp(user, db):
    """Generate a fresh OTP, store it on the user record, and return the plain OTP."""
    otp = generate_otp(current_app.config.get("OTP_LENGTH", 6))
    expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 10)
    user.otp_secret = otp                                          # stored plain for demo; hash in production
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    user.two_fa_verified = False
    db.session.commit()
    return otp


def verify_otp(user, submitted_otp: str) -> bool:
    """Return True if the submitted OTP matches and has not expired."""
    if not user.otp_secret or not user.otp_expiry:
        return False
    if datetime.utcnow() > user.otp_expiry:
        return False
    return secrets.compare_digest(user.otp_secret, submitted_otp.strip())
