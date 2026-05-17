"""
Admin panel routes — view users, login logs, and security events
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import User, LoginLog

admin_bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# Admin-only decorator
# ---------------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    locked_users = User.query.filter(User.locked_until != None).count()  # noqa: E711
    total_logs = LoginLog.query.count()
    recent_logs = (
        LoginLog.query
        .order_by(LoginLog.timestamp.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        locked_users=locked_users,
        total_logs=total_logs,
        recent_logs=recent_logs,
    )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    users_page = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/users.html", users_page=users_page)


@admin_bp.route("/users/<int:user_id>/unlock", methods=["POST"])
@login_required
@admin_required
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.reset_failed_attempts()
    db.session.commit()
    flash(f"User '{user.username}' has been unlocked.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    state = "activated" if user.is_active else "deactivated"
    flash(f"User '{user.username}' has been {state}.", "success")
    return redirect(url_for("admin.users"))


# ---------------------------------------------------------------------------
# Security logs
# ---------------------------------------------------------------------------

@admin_bp.route("/logs")
@login_required
@admin_required
def logs():
    page = request.args.get("page", 1, type=int)
    event_filter = request.args.get("event", "")
    query = LoginLog.query.order_by(LoginLog.timestamp.desc())
    if event_filter:
        query = query.filter(LoginLog.event_type == event_filter.upper())
    logs_page = query.paginate(page=page, per_page=30)
    event_types = ["SUCCESS", "FAILED", "LOCKED", "OTP_SENT", "OTP_SUCCESS", "OTP_FAILED", "LOGOUT", "REGISTER"]
    return render_template(
        "admin/logs.html",
        logs_page=logs_page,
        event_types=event_types,
        current_filter=event_filter.upper(),
    )
