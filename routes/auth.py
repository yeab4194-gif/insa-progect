"""
Authentication routes: register, login (with brute-force protection), 2FA OTP
"""

from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session, jsonify
)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from config import Config
from utils.password import check_password_strength, hash_password, verify_password
from utils.otp import set_user_otp, send_otp_email, verify_otp
from utils.logging import log_event

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- Basic validation ---
        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if password != confirm:
            errors.append("Passwords do not match.")

        # --- Password strength ---
        strength = check_password_strength(password)
        if strength["score"] < 3:
            errors.append(
                f"Password is too weak ({strength['level']}). "
                + " ".join(strength["suggestions"])
            )

        # --- Uniqueness ---
        if User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email is already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", username=username, email=email)

        # --- Create user ---
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.commit()

        log_event("REGISTER", username, user_id=user.id, details="New user registered")
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ---------------------------------------------------------------------------
# Password strength API (called via fetch from the registration form)
# ---------------------------------------------------------------------------

@auth_bp.route("/check-password-strength", methods=["POST"])
def check_strength_api():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    result = check_password_strength(password)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Login (step 1 — credentials)
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        # --- Account not found ---
        if not user:
            log_event("FAILED", username, details="Username not found")
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        # --- Account locked ---
        if user.is_locked():
            remaining = user.lockout_remaining_seconds()
            log_event("LOCKED", username, user_id=user.id,
                      details=f"Account locked, {remaining}s remaining")
            flash(
                f"Account is temporarily locked due to too many failed attempts. "
                f"Try again in {remaining // 60}m {remaining % 60}s.",
                "danger"
            )
            return render_template("login.html")

        # --- Wrong password ---
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            attempts_left = Config.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts

            if user.failed_login_attempts >= Config.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=Config.LOCKOUT_DURATION_MINUTES
                )
                db.session.commit()
                log_event("LOCKED", username, user_id=user.id,
                          details=f"Locked after {user.failed_login_attempts} failed attempts")
                flash(
                    f"Too many failed attempts. Account locked for "
                    f"{Config.LOCKOUT_DURATION_MINUTES} minutes.",
                    "danger"
                )
            else:
                db.session.commit()
                log_event("FAILED", username, user_id=user.id,
                          details=f"Wrong password, attempt {user.failed_login_attempts}")
                flash(
                    f"Invalid username or password. "
                    f"{attempts_left} attempt(s) remaining before lockout.",
                    "danger"
                )
            return render_template("login.html")

        # --- Credentials correct — send OTP ---
        user.reset_failed_attempts()
        otp = set_user_otp(user, db)

        email_sent = send_otp_email(user.email, user.username, otp)

        # Store user id in session for the OTP step
        session["pending_2fa_user_id"] = user.id
        session.permanent = True

        if email_sent:
            log_event("OTP_SENT", username, user_id=user.id,
                      details=f"OTP sent to {user.email}")
            flash(
                f"A 6-digit OTP has been sent to your email ({_mask_email(user.email)}). "
                f"It expires in {Config.OTP_EXPIRY_MINUTES} minutes.",
                "info"
            )
        else:
            # Email failed — show OTP in flash for demo/dev environments
            log_event("OTP_SENT", username, user_id=user.id,
                      details="OTP email failed; shown in flash (dev mode)")
            flash(
                f"Email delivery failed (check SMTP config). "
                f"[DEV MODE] Your OTP is: {otp}",
                "warning"
            )

        return redirect(url_for("auth.verify_otp_view"))

    return render_template("login.html")


# ---------------------------------------------------------------------------
# Login (step 2 — OTP verification)
# ---------------------------------------------------------------------------

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp_view():
    user_id = session.get("pending_2fa_user_id")
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        session.pop("pending_2fa_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        submitted_otp = request.form.get("otp", "").strip()

        if verify_otp(user, submitted_otp):
            # Clear OTP fields
            user.otp_secret = None
            user.otp_expiry = None
            user.two_fa_verified = True
            db.session.commit()

            session.pop("pending_2fa_user_id", None)
            login_user(user, remember=False)

            log_event("OTP_SUCCESS", user.username, user_id=user.id,
                      details="2FA verified, login complete")
            log_event("SUCCESS", user.username, user_id=user.id,
                      details="Login successful")

            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.index"))
        else:
            log_event("OTP_FAILED", user.username, user_id=user.id,
                      details="Wrong or expired OTP submitted")
            flash("Invalid or expired OTP. Please try again or request a new one.", "danger")

    return render_template("verify_otp.html", email=_mask_email(user.email))


# ---------------------------------------------------------------------------
# Resend OTP
# ---------------------------------------------------------------------------

@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    user_id = session.get("pending_2fa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for("auth.login"))

    otp = set_user_otp(user, db)
    email_sent = send_otp_email(user.email, user.username, otp)

    if email_sent:
        log_event("OTP_SENT", user.username, user_id=user.id, details="OTP resent")
        flash("A new OTP has been sent to your email.", "info")
    else:
        log_event("OTP_SENT", user.username, user_id=user.id,
                  details="OTP resend email failed; shown in flash (dev mode)")
        flash(f"Email delivery failed. [DEV MODE] Your OTP is: {otp}", "warning")

    return redirect(url_for("auth.verify_otp_view"))


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout")
@login_required
def logout():
    log_event("LOGOUT", current_user.username, user_id=current_user.id)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mask_email(email: str) -> str:
    """Partially mask an email for display: ab***@domain.com"""
    try:
        local, domain = email.split("@", 1)
        visible = local[:2] if len(local) >= 2 else local[0]
        return f"{visible}***@{domain}"
    except Exception:
        return "***"
