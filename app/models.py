
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default="canvasser")
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_address = db.Column(db.String(255), unique=True, nullable=False)
    house_number = db.Column(db.String(50))
    street_name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(20), default="FL")
    zipcode = db.Column(db.String(20))
    county = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    current_status = db.Column(db.String(50), default="Door Knocked")
    total_visits = db.Column(db.Integer, default=0)
    last_visit_at = db.Column(db.DateTime)
    last_visited_by = db.Column(db.String(120))

    owner_name = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    alternate_phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    preferred_language = db.Column(db.String(50))
    insurance_company = db.Column(db.String(120))
    policy_name_or_type = db.Column(db.String(120))
    prior_claim = db.Column(db.String(50))
    prior_claim_details = db.Column(db.Text)
    roof_age = db.Column(db.String(20))
    home_year = db.Column(db.String(20))
    years_in_house = db.Column(db.String(20))
    property_type = db.Column(db.String(50))
    damage_type = db.Column(db.String(120))
    damage_details = db.Column(db.Text)
    best_time_to_contact = db.Column(db.String(120))
    owner_objections = db.Column(db.Text)
    conversation_summary = db.Column(db.Text)
    notes = db.Column(db.Text)
    assigned_to = db.Column(db.String(120))
    follow_up_date = db.Column(db.Date)
    inspection_date = db.Column(db.Date)
    inspection_time = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    visits = db.relationship("Visit", backref="property", cascade="all, delete-orphan")
    followups = db.relationship("FollowUp", backref="property", cascade="all, delete-orphan")
    call_logs = db.relationship("CallLog", backref="property", cascade="all, delete-orphan")
    attachments = db.relationship("Attachment", backref="property", cascade="all, delete-orphan")
    status_history = db.relationship("StatusHistory", backref="property", cascade="all, delete-orphan")

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
    visited_by = db.Column(db.String(120), nullable=False)
    result_status = db.Column(db.String(50), nullable=False)
    roof_damage_visible = db.Column(db.Boolean, default=False)
    flyer_left = db.Column(db.Boolean, default=False)
    gate_closed = db.Column(db.Boolean, default=False)
    tarp_visible = db.Column(db.Boolean, default=False)
    exterior_damage_visible = db.Column(db.Boolean, default=False)
    water_stain_visible = db.Column(db.Boolean, default=False)
    cars_in_driveway = db.Column(db.String(20))
    quick_note = db.Column(db.Text)
    gps_latitude = db.Column(db.Float)
    gps_longitude = db.Column(db.Float)
    visited_at = db.Column(db.DateTime, default=datetime.utcnow)

class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
    assigned_to = db.Column(db.String(120), nullable=False)
    follow_up_date = db.Column(db.Date, nullable=False)
    follow_up_type = db.Column(db.String(50), nullable=False)
    next_action = db.Column(db.String(255))
    result = db.Column(db.String(50), default="pending")
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
    called_by = db.Column(db.String(120), nullable=False)
    call_result = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    next_action = db.Column(db.String(255))
    next_follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    uploaded_by = db.Column(db.String(120), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"))
    recipient_email = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(db.String(120), nullable=False)
    change_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
