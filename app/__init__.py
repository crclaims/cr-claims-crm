import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import inspect, text

db = SQLAlchemy()
login_manager = LoginManager()


def ensure_property_columns():
    inspector = inspect(db.engine)
    columns = {col["name"] for col in inspector.get_columns("property")}

    statements = []

    if "lead_result" not in columns:
        statements.append('ALTER TABLE property ADD COLUMN lead_result VARCHAR(120)')
    if "next_action" not in columns:
        statements.append('ALTER TABLE property ADD COLUMN next_action VARCHAR(255)')
    if "assigned_to" not in columns:
        statements.append('ALTER TABLE property ADD COLUMN assigned_to VARCHAR(120)')
    if "follow_up_date" not in columns:
        statements.append('ALTER TABLE property ADD COLUMN follow_up_date DATE')
    if "inspection_date" not in columns:
        statements.append('ALTER TABLE property ADD COLUMN inspection_date DATE')
    if "inspection_time" not in columns:
        statements.append('ALTER TABLE property ADD COLUMN inspection_time VARCHAR(20)')

    for stmt in statements:
        db.session.execute(text(stmt))

    if statements:
        db.session.commit()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///cr_claims_production.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", os.path.join(app.instance_path, "uploads"))
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        ensure_property_columns()

    return app
