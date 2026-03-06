from app import create_app, db
from app.models import User
import os

app = create_app()

with app.app_context():
    db.create_all()
    temp_password = os.getenv("ADMIN_TEMP_PASSWORD", "2lau#NnQYR2qIojbKphS")
    users = [
        ("Elizabeth", "JD.claimsresolution@gmail.com", "admin"),
        ("Genesis", "genesis@local.crm", "canvasser"),
        ("Jesus", "jesus@local.crm", "caller"),
    ]
    for full_name, email, role in users:
    u = User.query.filter_by(email=email).first()
    if not u:
        u = User(full_name=full_name, email=email, role=role)
        db.session.add(u)

    if email == "JD.claimsresolution@gmail.com":
        u.full_name = full_name
        u.role = "admin"
        u.active = True
        u.set_password(temp_password)

db.session.commit()
