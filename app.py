"""
Secure Authentication System
Flask application entry point
"""

import os
from flask import Flask
from extensions import db, login_manager, mail
from config import Config
from models import User
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.main import main_bp


def create_app():
    application = Flask(__name__)
    application.config.from_object(Config)

    # Initialize extensions
    db.init_app(application)
    login_manager.init_app(application)
    mail.init_app(application)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    application.register_blueprint(main_bp)
    application.register_blueprint(auth_bp, url_prefix="/auth")
    application.register_blueprint(admin_bp, url_prefix="/admin")

    # Create tables
    with application.app_context():
        db.create_all()

    return application


# Module-level app variable — required by Gunicorn ("gunicorn app:app")
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
