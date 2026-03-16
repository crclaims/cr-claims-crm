
import csv
import io
import os
from datetime import datetime
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for, Response
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from . import db
from .models import User, Property, Visit, FollowUp, CallLog, Attachment, Notification, StatusHistory

bp = Blueprint("main", __name__)

STATUSES = [
    "Door Knocked & Flyer Left",
    "No Answer",
    "Follow Up",
    "Text",
    "Talk",
    "Possible Prospect",
    "Inspection Scheduled",
    "Inspection Completed",
    "Signed LOR",
    "Claims Opened",
    "Not Interest"
]

STATUS_COLORS = {
    "Door Knocked & Flyer Left": "#7A1E3A",   # rojo vino
    "No Answer": "#F4D35E",                   # amarillo
    "Follow Up": "#C99700",                   # mostaza
    "Text": "#7BD389",                        # verde claro
    "Talk": "#1B5E20",                        # verde oscuro
    "Possible Prospect": "#F28C28",           # naranja
    "Inspection Scheduled": "#D9D9D9",        # gris claro
    "Inspection Completed": "#7EC8E3",        # azul claro
    "Signed LOR": "#0B3D91",                  # azul marino
    "Claims Opened": "#7B2CBF",               # púrpura
    "Not Interest": "#C62828"                 # rojo
}
  
@bp.app_context_processor
def inject_globals():
    unread = Notification.query.filter_by(is_read=False).count() if current_user.is_authenticated else 0
    return {"STATUSES": STATUSES, "unread_notifications": unread, "GOOGLE_MAPS_API_KEY": current_app.config.get("GOOGLE_MAPS_API_KEY")}

def notify(type_, title, message, property_id=None, recipient_email="JD.claimsresolution@gmail.com"):
    n = Notification(
        type=type_,
        title=title,
        message=message,
        property_id=property_id,
        recipient_email=recipient_email,
    )
    db.session.add(n)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Bienvenida/o, {user.full_name}.")
            return redirect(url_for("main.dashboard"))
        flash("Credenciales inválidas.")
    return render_template("login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

@bp.route("/")
@login_required
def dashboard():
    stats = {
        "properties": Property.query.count(),
        "followups": FollowUp.query.filter_by(result="pending").count(),
        "inspections": Property.query.filter_by(current_status="Inspection Scheduled").count(),
        "signed": Property.query.filter_by(current_status="Signed LOR").count(),
        "visits_today": Visit.query.filter(db.func.date(Visit.visited_at) == datetime.utcnow().date()).count(),
        "calls_today": CallLog.query.filter(db.func.date(CallLog.created_at) == datetime.utcnow().date()).count(),
    }
    recent = Property.query.order_by(Property.updated_at.desc()).limit(12).all()
    todays_followups = FollowUp.query.filter(
        db.func.date(FollowUp.follow_up_date) == datetime.utcnow().date(),
        FollowUp.result == "pending"
    ).order_by(FollowUp.follow_up_date.asc()).limit(10).all()
    return render_template("dashboard.html", stats=stats, recent=recent, todays_followups=todays_followups)

@bp.route("/properties")
@login_required
def properties():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    assigned = request.args.get("assigned", "").strip()
    query = Property.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Property.full_address.ilike(like),
                Property.owner_name.ilike(like),
                Property.phone.ilike(like),
                Property.insurance_company.ilike(like)
            )
        )
    if status:
        query = query.filter_by(current_status=status)
    if assigned:
        query = query.filter_by(assigned_to=assigned)
    rows = query.order_by(Property.updated_at.desc()).all()
    assignees = User.query.order_by(User.full_name).all()
    return render_template("properties.html", rows=rows, q=q, status=status, assigned=assigned, assignees=assignees)

@bp.route("/property/new", methods=["GET", "POST"])
@login_required
def property_new():
    users = User.query.filter_by(active=True).order_by(User.full_name).all()
    if request.method == "POST":
        form = request.form
        full_address = form.get("full_address", "").strip()
        if not full_address:
            flash("La dirección es obligatoria.")
            return redirect(url_for("main.property_new"))

        existing = Property.query.filter(db.func.lower(Property.full_address) == full_address.lower()).first()
        if existing:
            flash(f"Esta casa ya existe. Visitas: {existing.total_visits} | Última visita: {existing.last_visit_at} por {existing.last_visited_by}")
            return redirect(url_for("main.property_view", property_id=existing.id))

        p = Property(
            full_address=full_address,
            house_number=form.get("house_number"),
            street_name=form.get("street_name"),
            city=form.get("city"),
            state=form.get("state", "FL"),
            zipcode=form.get("zipcode"),
            county=form.get("county"),
            latitude=float(form.get("latitude")) if form.get("latitude") else None,
            longitude=float(form.get("longitude")) if form.get("longitude") else None,
            current_status=form.get("current_status"),
            total_visits=1,
            last_visit_at=datetime.utcnow(),
            last_visited_by=current_user.full_name,
            owner_name=form.get("owner_name"),
            phone=form.get("phone"),
            alternate_phone=form.get("alternate_phone"),
            email=form.get("email"),
            preferred_language=form.get("preferred_language"),
            insurance_company=form.get("insurance_company"),
            policy_name_or_type=form.get("policy_name_or_type"),
            prior_claim=form.get("prior_claim"),
            prior_claim_details=form.get("prior_claim_details"),
            roof_age=form.get("roof_age"),
            home_year=form.get("home_year"),
            years_in_house=form.get("years_in_house"),
            property_type=form.get("property_type"),
            damage_type=form.get("damage_type"),
            damage_details=form.get("damage_details"),
           owner_objections=form.get("owner_objections"),
           conversation_summary=form.get("conversation_summary"),
           notes=form.get("notes"),
           lead_result=form.get("lead_result"),
           next_action=form.get("next_action"),
           assigned_to=form.get("assigned_to"),
           follow_up_date=datetime.strptime(form.get("follow_up_date"), "%Y-%m-%d").date() if form.get("follow_up_date") else None,
            inspection_date=datetime.strptime(form.get("inspection_date"), "%Y-%m-%d").date() if form.get("inspection_date") else None,
            inspection_time=form.get("inspection_time"),
        )
        db.session.add(p)
        db.session.flush()

        visit = Visit(
            property_id=p.id,
            visited_by=current_user.full_name,
            result_status=form.get("current_status"),
            roof_damage_visible=bool(form.get("roof_damage_visible")),
            flyer_left=bool(form.get("flyer_left")),
            gate_closed=bool(form.get("gate_closed")),
            tarp_visible=bool(form.get("tarp_visible")),
            exterior_damage_visible=bool(form.get("exterior_damage_visible")),
            water_stain_visible=bool(form.get("water_stain_visible")),
            cars_in_driveway=form.get("cars_in_driveway"),
            quick_note=form.get("quick_note"),
            gps_latitude=float(form.get("latitude")) if form.get("latitude") else None,
            gps_longitude=float(form.get("longitude")) if form.get("longitude") else None,
        )
        db.session.add(visit)

        db.session.add(StatusHistory(
            property_id=p.id,
            old_status=None,
            new_status=form.get("current_status"),
            changed_by=current_user.full_name,
            change_note=form.get("quick_note"),
        ))

        if form.get("follow_up_date"):
            db.session.add(FollowUp(
                property_id=p.id,
                assigned_to=form.get("assigned_to") or current_user.full_name,
                follow_up_date=datetime.strptime(form.get("follow_up_date"), "%Y-%m-%d").date(),
                follow_up_type=form.get("follow_up_type") or "second_visit",
                next_action=form.get("next_action"),
                notes=form.get("notes"),
                created_by=current_user.full_name,
            ))
            notify("follow_up", "Nuevo follow-up", f"Follow-up creado para {p.full_address} el {form.get('follow_up_date')}.", p.id)

        if form.get("inspection_date"):
            notify("inspection", "Nueva inspección", f"Inspección programada para {p.full_address} el {form.get('inspection_date')} {form.get('inspection_time') or ''}.", p.id)

        db.session.commit()
        flash("Casa registrada correctamente.")
        return redirect(url_for("main.property_view", property_id=p.id))

    return render_template("property_form.html", users=users)

@bp.route("/property/<int:property_id>")
@login_required
def property_view(property_id):
    row = Property.query.get_or_404(property_id)
    visits = Visit.query.filter_by(property_id=property_id).order_by(Visit.visited_at.desc()).all()
    history = StatusHistory.query.filter_by(property_id=property_id).order_by(StatusHistory.created_at.desc()).all()
    followups = FollowUp.query.filter_by(property_id=property_id).order_by(FollowUp.follow_up_date.desc()).all()
    calls = CallLog.query.filter_by(property_id=property_id).order_by(CallLog.created_at.desc()).all()
    attachments = Attachment.query.filter_by(property_id=property_id).order_by(Attachment.uploaded_at.desc()).all()
    users = User.query.filter_by(active=True).order_by(User.full_name).all()
    return render_template("property_view.html", row=row, visits=visits, history=history, followups=followups, calls=calls, attachments=attachments, users=users)

@bp.route("/property/<int:property_id>/edit", methods=["GET", "POST"])
@login_required
def property_edit(property_id):
    row = Property.query.get_or_404(property_id)
    users = User.query.filter_by(active=True).order_by(User.full_name).all()
    if request.method == "POST":
        form = request.form
        old_status = row.current_status
        row.owner_name = form.get("owner_name")
        row.phone = form.get("phone")
        row.alternate_phone = form.get("alternate_phone")
        row.email = form.get("email")
        row.preferred_language = form.get("preferred_language")
        row.insurance_company = form.get("insurance_company")
        row.policy_name_or_type = form.get("policy_name_or_type")
        row.prior_claim = form.get("prior_claim")
        row.prior_claim_details = form.get("prior_claim_details")
        row.roof_age = form.get("roof_age")
        row.home_year = form.get("home_year")
        row.years_in_house = form.get("years_in_house")
        row.property_type = form.get("property_type")
        row.damage_type = form.get("damage_type")
        row.damage_details = form.get("damage_details")
        row.best_time_to_contact = form.get("best_time_to_contact")
        row.owner_objections = form.get("owner_objections")
        row.conversation_summary = form.get("conversation_summary")
        row.notes = form.get("notes")
        row.lead_result = form.get("lead_result")
        row.next_action = form.get("next_action")
        row.assigned_to = form.get("assigned_to")
        row.current_status = form.get("current_status")
        row.follow_up_date = datetime.strptime(form.get("follow_up_date"), "%Y-%m-%d").date() if form.get("follow_up_date") else None
        row.inspection_date = datetime.strptime(form.get("inspection_date"), "%Y-%m-%d").date() if form.get("inspection_date") else None
        row.inspection_time = form.get("inspection_time")
        if old_status != row.current_status:
            db.session.add(StatusHistory(
                property_id=row.id,
                old_status=old_status,
                new_status=row.current_status,
                changed_by=current_user.full_name,
                change_note="Edición de lead",
            ))
        db.session.commit()
        flash("Lead actualizado.")
        return redirect(url_for("main.property_view", property_id=row.id))
    return render_template("property_edit.html", row=row, users=users)

@bp.route("/property/<int:property_id>/visit", methods=["POST"])
@login_required
def add_visit(property_id):
    row = Property.query.get_or_404(property_id)
    form = request.form
    old_status = row.current_status

    visit = Visit(
        property_id=row.id,
        visited_by=form.get("visited_by"),
        result_status=form.get("result_status"),
        roof_damage_visible=bool(form.get("roof_damage_visible")),
        flyer_left=bool(form.get("flyer_left")),
        gate_closed=bool(form.get("gate_closed")),
        tarp_visible=bool(form.get("tarp_visible")),
        exterior_damage_visible=bool(form.get("exterior_damage_visible")),
        water_stain_visible=bool(form.get("water_stain_visible")),
        cars_in_driveway=form.get("cars_in_driveway"),
        quick_note=form.get("quick_note"),
    )
    db.session.add(visit)

    row.current_status = form.get("result_status")
    row.total_visits = (row.total_visits or 0) + 1
    row.last_visit_at = datetime.utcnow()
    row.last_visited_by = form.get("visited_by")
    row.updated_at = datetime.utcnow()
    row.assigned_to = form.get("assigned_to") or row.assigned_to
    if form.get("property_notes"):
        row.notes = form.get("property_notes")
    if form.get("follow_up_date"):
        row.follow_up_date = datetime.strptime(form.get("follow_up_date"), "%Y-%m-%d").date()
        db.session.add(FollowUp(
            property_id=row.id,
            assigned_to=form.get("assigned_to") or form.get("visited_by"),
            follow_up_date=row.follow_up_date,
            follow_up_type=form.get("follow_up_type") or "second_visit",
            next_action=form.get("next_action"),
            notes=form.get("quick_note"),
            created_by=form.get("visited_by"),
        ))
        notify("follow_up", "Nuevo follow-up", f"Follow-up creado para {row.full_address} el {form.get('follow_up_date')}.", row.id)

    if form.get("inspection_date"):
        row.inspection_date = datetime.strptime(form.get("inspection_date"), "%Y-%m-%d").date()
        row.inspection_time = form.get("inspection_time")
        notify("inspection", "Nueva inspección", f"Inspección programada para {row.full_address} el {form.get('inspection_date')} {form.get('inspection_time') or ''}.", row.id)

    if old_status != row.current_status:
        db.session.add(StatusHistory(
            property_id=row.id,
            old_status=old_status,
            new_status=row.current_status,
            changed_by=form.get("visited_by"),
            change_note=form.get("quick_note"),
        ))

    db.session.commit()
    flash("Visita agregada.")
    return redirect(url_for("main.property_view", property_id=row.id))

@bp.route("/property/<int:property_id>/call", methods=["POST"])
@login_required
def add_call_log(property_id):
    row = Property.query.get_or_404(property_id)
    form = request.form
    call = CallLog(
        property_id=row.id,
        called_by=current_user.full_name,
        call_result=form.get("call_result"),
        notes=form.get("notes"),
        next_action=form.get("next_action"),
        next_follow_up_date=datetime.strptime(form.get("next_follow_up_date"), "%Y-%m-%d").date() if form.get("next_follow_up_date") else None,
    )
    db.session.add(call)
    if form.get("next_follow_up_date"):
        db.session.add(FollowUp(
            property_id=row.id,
            assigned_to=current_user.full_name,
            follow_up_date=call.next_follow_up_date,
            follow_up_type="call",
            next_action=form.get("next_action"),
            notes=form.get("notes"),
            created_by=current_user.full_name,
        ))
        notify("follow_up", "Follow-up por llamada", f"Follow-up creado desde call log para {row.full_address} el {form.get('next_follow_up_date')}.", row.id)
    db.session.commit()
    flash("Llamada registrada.")
    return redirect(url_for("main.property_view", property_id=row.id))

@bp.route("/property/<int:property_id>/upload", methods=["POST"])
@login_required
def upload_attachment(property_id):
    row = Property.query.get_or_404(property_id)
    file = request.files.get("file")
    file_type = request.form.get("file_type") or "other"
    if not file or file.filename == "":
        flash("Debes seleccionar un archivo.")
        return redirect(url_for("main.property_view", property_id=row.id))

    fname = secure_filename(file.filename)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    saved_name = f"{row.id}_{ts}_{fname}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_name)
    file.save(save_path)

    attachment = Attachment(
        property_id=row.id,
        file_name=fname,
        file_path=save_path,
        file_type=file_type,
        uploaded_by=current_user.full_name,
    )
    db.session.add(attachment)
    db.session.commit()
    flash("Archivo subido.")
    return redirect(url_for("main.property_view", property_id=row.id))

@bp.route("/attachment/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    row = Attachment.query.get_or_404(attachment_id)
    return send_file(row.file_path, as_attachment=True, download_name=row.file_name)

@bp.route("/followups")
@login_required
def followups():
    rows = FollowUp.query.order_by(FollowUp.follow_up_date.asc()).all()
    return render_template("followups.html", rows=rows)

@bp.route("/followup/<int:followup_id>/complete", methods=["POST"])
@login_required
def followup_complete(followup_id):
    row = FollowUp.query.get_or_404(followup_id)
    row.result = "completed"
    db.session.commit()
    flash("Follow-up marcado como completado.")
    return redirect(url_for("main.followups"))

@bp.route("/notifications")
@login_required
def notifications():
    rows = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", rows=rows)

@bp.route("/notification/<int:notification_id>/read", methods=["POST"])
@login_required
def notification_read(notification_id):
    row = Notification.query.get_or_404(notification_id)
    row.is_read = True
    db.session.commit()
    return redirect(url_for("main.notifications"))

@bp.route("/reports")
@login_required
def reports():
    visits_by_user = db.session.query(Visit.visited_by, db.func.count(Visit.id).label("total")).group_by(Visit.visited_by).order_by(db.desc("total")).all()
    signed_by_assignee = db.session.query(Property.assigned_to, db.func.count(Property.id).label("total")).filter(Property.current_status=="Signed LOR").group_by(Property.assigned_to).order_by(db.desc("total")).all()
    status_breakdown = db.session.query(Property.current_status, db.func.count(Property.id).label("total")).group_by(Property.current_status).order_by(db.desc("total")).all()
    return render_template("reports.html", visits_by_user=visits_by_user, signed_by_assignee=signed_by_assignee, status_breakdown=status_breakdown)

@bp.route("/export/properties.csv")
@login_required
def export_properties():
    rows = Property.query.order_by(Property.updated_at.desc()).all()
    output = io.StringIO()

    fieldnames = [
        "id",
        "full_address",
        "city",
        "state",
        "zipcode",
        "current_status",
        "owner_name",
        "phone",
        "insurance_company",
        "roof_age",
        "years_in_house",
        "assigned_to",
        "lead_result",
        "next_action",
        "follow_up_date",
        "inspection_date",
        "last_visit_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in rows:
        writer.writerow({
            "id": r.id,
            "full_address": r.full_address,
            "city": r.city,
            "state": r.state,
            "zipcode": r.zipcode,
            "current_status": r.current_status,
            "owner_name": r.owner_name,
            "phone": r.phone,
            "insurance_company": r.insurance_company,
            "roof_age": r.roof_age,
            "years_in_house": r.years_in_house,
            "assigned_to": r.assigned_to,
            "lead_result": r.lead_result,
            "next_action": r.next_action,
            "follow_up_date": r.follow_up_date,
            "inspection_date": r.inspection_date,
            "last_visit_at": r.last_visit_at,
        })

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cr_properties_export.csv"},
    )
@bp.route("/map")
@login_required
def map_view():
    return render_template("map.html")

@bp.route("/api/properties")
@login_required
def api_properties():
    rows = Property.query.all()
    data = []
    for r in rows:
        if r.latitude is None or r.longitude is None:
            continue
        data.append({
            "id": r.id,
            "address": r.full_address,
            "status": r.current_status,
            "color": STATUS_COLORS.get(r.current_status, "gray"),
            "lat": r.latitude,
            "lng": r.longitude,
            "total_visits": r.total_visits,
            "last_visit_at": r.last_visit_at.isoformat() if r.last_visit_at else "",
            "last_visited_by": r.last_visited_by or "",
            "owner_name": r.owner_name or "",
        })
    return jsonify(data)
@bp.route("/api/properties/nearby")
@login_required
def api_properties_nearby():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius_m = request.args.get("radius_m", default=50, type=float)

    if lat is None or lng is None:
        return jsonify([])

    lat_delta = radius_m / 111320.0
    lng_delta = radius_m / 111320.0

    candidates = Property.query.filter(
        Property.latitude.isnot(None),
        Property.longitude.isnot(None),
        Property.latitude >= lat - lat_delta,
        Property.latitude <= lat + lat_delta,
        Property.longitude >= lng - lng_delta,
        Property.longitude <= lng + lng_delta
    ).all()

    data = []

    for r in candidates:
        dlat_m = (r.latitude - lat) * 111320.0
        dlng_m = (r.longitude - lng) * 111320.0
        distance_m = ((dlat_m * dlat_m) + (dlng_m * dlng_m)) ** 0.5

        if distance_m <= radius_m:
            data.append({
                "id": r.id,
                "address": r.full_address,
                "status": r.current_status,
                "color": STATUS_COLORS.get(r.current_status, "gray"),
                "lat": r.latitude,
                "lng": r.longitude,
                "distance_m": round(distance_m, 1),
                "total_visits": r.total_visits,
                "last_visit_at": r.last_visit_at.isoformat() if r.last_visit_at else "",
                "last_visited_by": r.last_visited_by or "",
                "owner_name": r.owner_name or ""
            })

    data.sort(key=lambda x: x["distance_m"])
    return jsonify(data)
@bp.route("/agenda")
@login_required
def agenda():
    followups = Property.query.filter(Property.follow_up_date.isnot(None)).order_by(Property.follow_up_date.asc()).all()
    inspections = Property.query.filter(Property.inspection_date.isnot(None)).order_by(Property.inspection_date.asc()).all()
    return render_template("agenda.html", followups=followups, inspections=inspections)
