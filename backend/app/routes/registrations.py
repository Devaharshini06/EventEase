import csv
import io
from flask import Blueprint, request, jsonify, Response
from flask_security import current_user
from sqlalchemy import or_
from ..models import db, Event, Registration, User
from ..services import (
    register_attendee_for_event,
    cancel_registration,
    check_in_registration,
)
from . import token_auth_required, roles_required_json

registrations_bp = Blueprint("registrations_api", __name__, url_prefix="/api")


def _can_manage_event_registrations(user, event: Event) -> bool:
    if not user or not user.is_authenticated or not user.active:
        return False
    if user.has_role_name("admin"):
        return True
    return user.has_role_name("organizer") and event.organizer_id == user.id


@registrations_bp.route("/events/<int:event_id>/registrations", methods=["POST"])
@token_auth_required
def create_event_registration(event_id: int):
    data = request.get_json(silent=True) or {}
    notes = data.get("notes")
    registration, error, status_code = register_attendee_for_event(
        event_id=event_id,
        user=current_user,
        notes=notes,
    )
    if error:
        return jsonify({"error": error}), status_code

    return (
        jsonify(
            {
                "message": "Registration confirmed.",
                "registration": registration.to_dict(include_event=True, include_attendee=True),
            }
        ),
        201,
    )


@registrations_bp.route("/registrations/me", methods=["GET"])
@token_auth_required
def list_my_registrations():
    status_filter = request.args.get("status", "").strip().upper()
    query = Registration.query.filter_by(attendee_id=current_user.id)

    if status_filter and status_filter != "ALL":
        query = query.filter_by(status=status_filter)

    registrations = query.order_by(Registration.registered_at.desc()).all()
    return (
        jsonify(
            {
                "registrations": [
                    r.to_dict(include_event=True, include_attendee=False) for r in registrations
                ]
            }
        ),
        200,
    )


@registrations_bp.route("/events/<int:event_id>/registrations", methods=["GET"])
@roles_required_json("organizer", "admin")
def list_event_registrations(event_id: int):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found."}), 404

    if not _can_manage_event_registrations(current_user, event):
        return (
            jsonify(
                {"error": "You do not have permission to view registrations for this event."}
            ),
            403,
        )

    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip().upper()

    query = Registration.query.join(User, Registration.attendee_id == User.id).filter(
        Registration.event_id == event.id
    )

    if status_filter and status_filter != "ALL":
        query = query.filter(Registration.status == status_filter)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                User.organization.ilike(pattern),
                Registration.registration_reference.ilike(pattern),
            )
        )

    registrations = query.order_by(Registration.registered_at.desc()).all()

    all_for_event = Registration.query.filter_by(event_id=event.id).all()
    confirmed_count = sum(1 for r in all_for_event if r.status == "CONFIRMED")
    checked_in_count = sum(1 for r in all_for_event if r.status == "CHECKED_IN")
    cancelled_count = sum(1 for r in all_for_event if r.status == "CANCELLED")

    return (
        jsonify(
            {
                "event": event.to_dict(include_stats=True),
                "registrations": [
                    r.to_dict(include_event=False, include_attendee=True) for r in registrations
                ],
                "summary": {
                    "active_registered_count": confirmed_count + checked_in_count,
                    "confirmed_count": confirmed_count,
                    "checked_in_count": checked_in_count,
                    "cancelled_count": cancelled_count,
                    "remaining_capacity": event.remaining_capacity,
                    "capacity": event.capacity,
                },
            }
        ),
        200,
    )


@registrations_bp.route("/events/<int:event_id>/registrations/export", methods=["GET"])
@roles_required_json("organizer", "admin")
def export_event_registrations_csv(event_id: int):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found."}), 404

    if not _can_manage_event_registrations(current_user, event):
        return (
            jsonify(
                {"error": "You do not have permission to export registrations for this event."}
            ),
            403,
        )

    registrations = (
        Registration.query.filter_by(event_id=event.id)
        .order_by(Registration.registered_at.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Registration Reference",
            "Attendee Name",
            "Attendee Email",
            "Organization",
            "Phone",
            "Status",
            "Registered At (UTC)",
            "Checked In At (UTC)",
            "Cancelled At (UTC)",
            "Notes",
        ]
    )
    for reg in registrations:
        writer.writerow(
            [
                reg.registration_reference,
                reg.attendee.full_name if reg.attendee else "",
                reg.attendee.email if reg.attendee else "",
                reg.attendee.organization or "" if reg.attendee else "",
                reg.attendee.phone or "" if reg.attendee else "",
                reg.status,
                reg.registered_at.isoformat() if reg.registered_at else "",
                reg.checked_in_at.isoformat() if reg.checked_in_at else "",
                reg.cancelled_at.isoformat() if reg.cancelled_at else "",
                reg.notes or "",
            ]
        )

    csv_content = output.getvalue()
    output.close()

    filename = f"event_{event.id}_attendees.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@registrations_bp.route("/registrations/<int:registration_id>", methods=["GET"])
@token_auth_required
def get_registration_detail(registration_id: int):
    registration = db.session.get(Registration, registration_id)
    if not registration:
        return jsonify({"error": "Registration not found."}), 404

    event = registration.event
    is_owner = registration.attendee_id == current_user.id
    can_manage = _can_manage_event_registrations(current_user, event) if event else False

    if not (is_owner or can_manage):
        return (
            jsonify({"error": "You do not have permission to view this registration record."}),
            403,
        )

    return (
        jsonify(
            {
                "registration": registration.to_dict(
                    include_event=True, include_attendee=True
                )
            }
        ),
        200,
    )


@registrations_bp.route("/registrations/<int:registration_id>/cancel", methods=["POST"])
@token_auth_required
def cancel_registration_endpoint(registration_id: int):
    registration, error, status_code = cancel_registration(
        registration_id=registration_id,
        acting_user=current_user,
    )
    if error:
        return jsonify({"error": error}), status_code

    return (
        jsonify(
            {
                "message": "Registration cancelled successfully.",
                "registration": registration.to_dict(
                    include_event=True, include_attendee=True
                ),
            }
        ),
        200,
    )


@registrations_bp.route("/registrations/<int:registration_id>/check-in", methods=["POST"])
@roles_required_json("organizer", "admin")
def check_in_by_id_endpoint(registration_id: int):
    registration, error, status_code = check_in_registration(
        acting_user=current_user,
        registration_id=registration_id,
    )
    if error:
        return jsonify({"error": error}), status_code

    return (
        jsonify(
            {
                "message": "Attendee checked in successfully.",
                "registration": registration.to_dict(
                    include_event=True, include_attendee=True
                ),
            }
        ),
        200,
    )


@registrations_bp.route("/events/<int:event_id>/check-in", methods=["POST"])
@roles_required_json("organizer", "admin")
def check_in_by_reference_endpoint(event_id: int):
    data = request.get_json(silent=True) or {}
    reference = str(data.get("registration_reference", "")).strip()
    reg_id = data.get("registration_id")

    if not reference and reg_id is None:
        return (
            jsonify(
                {"error": "Provide either registration_reference or registration_id for check-in."}
            ),
            400,
        )

    registration, error, status_code = check_in_registration(
        acting_user=current_user,
        registration_id=int(reg_id) if reg_id is not None else None,
        registration_reference=reference if reference else None,
        event_id=event_id,
    )
    if error:
        return jsonify({"error": error}), status_code

    return (
        jsonify(
            {
                "message": "Attendee checked in successfully.",
                "registration": registration.to_dict(
                    include_event=True, include_attendee=True
                ),
            }
        ),
        200,
    )
