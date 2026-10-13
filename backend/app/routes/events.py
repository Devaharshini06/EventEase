from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_security import current_user
from sqlalchemy import or_
from ..models import db, Event, Category, Registration
from ..schemas import validate_event_payload, parse_iso_datetime
from . import roles_required_json

events_bp = Blueprint("events_api", __name__, url_prefix="/api/events")


def _can_manage_event(user, event: Event) -> bool:
    if not user or not user.is_authenticated or not user.active:
        return False
    if user.has_role_name("admin"):
        return True
    return user.has_role_name("organizer") and event.organizer_id == user.id


@events_bp.route("", methods=["GET"])
def list_events():
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", "").strip()
    city = request.args.get("city", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    price_type = request.args.get("price_type", "").strip().lower()  # free, paid
    availability = request.args.get("availability", "").strip().lower()  # open, all
    status_param = request.args.get("status", "").strip().upper()
    mine = request.args.get("mine", "false").lower() == "true"
    sort_by = request.args.get("sort_by", "date_asc").strip().lower()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    try:
        page_size = min(50, max(1, int(request.args.get("page_size", 9))))
    except ValueError:
        page_size = 9

    query = Event.query

    is_admin = current_user.is_authenticated and current_user.active and current_user.has_role_name("admin")
    is_organizer = (
        current_user.is_authenticated
        and current_user.active
        and current_user.has_role_name("organizer")
    )

    if mine:
        if not (is_organizer or is_admin):
            return jsonify({"error": "Organizer or administrator authentication required."}), 403
        if not is_admin or request.args.get("scope") == "own":
            query = query.filter(Event.organizer_id == current_user.id)
        if status_param and status_param != "ALL":
            query = query.filter(Event.status == status_param)
    elif is_admin and status_param:
        if status_param != "ALL":
            query = query.filter(Event.status == status_param)
    else:
        query = query.filter(Event.status == "PUBLISHED")

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Event.title.ilike(pattern),
                Event.description.ilike(pattern),
                Event.venue.ilike(pattern),
                Event.city.ilike(pattern),
            )
        )

    if category_id:
        try:
            query = query.filter(Event.category_id == int(category_id))
        except ValueError:
            return jsonify({"error": "Invalid category_id parameter."}), 400

    if city:
        query = query.filter(db.func.lower(Event.city) == city.lower())

    if start_date:
        parsed_start = parse_iso_datetime(start_date)
        if not parsed_start:
            return jsonify({"error": "Invalid start_date parameter."}), 400
        query = query.filter(Event.start_datetime >= parsed_start)

    if end_date:
        parsed_end = parse_iso_datetime(end_date)
        if not parsed_end:
            return jsonify({"error": "Invalid end_date parameter."}), 400
        query = query.filter(Event.start_datetime <= parsed_end)

    if price_type == "free":
        query = query.filter(Event.price == 0)
    elif price_type == "paid":
        query = query.filter(Event.price > 0)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if availability == "open":
        query = query.filter(
            Event.status == "PUBLISHED",
            Event.registered_count < Event.capacity,
            Event.registration_deadline > now,
            Event.end_datetime > now,
        )

    if sort_by == "date_desc":
        query = query.order_by(Event.start_datetime.desc())
    elif sort_by == "title_asc":
        query = query.order_by(Event.title.asc())
    elif sort_by == "capacity_desc":
        query = query.order_by((Event.capacity - Event.registered_count).desc())
    elif sort_by == "price_asc":
        query = query.order_by(Event.price.asc(), Event.start_datetime.asc())
    elif sort_by == "created_desc":
        query = query.order_by(Event.created_at.desc())
    else:
        query = query.order_by(Event.start_datetime.asc())

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    events = query.offset((page - 1) * page_size).limit(page_size).all()

    distinct_cities_rows = (
        db.session.query(Event.city)
        .filter(Event.status == "PUBLISHED")
        .distinct()
        .order_by(Event.city.asc())
        .all()
    )
    cities = [row[0] for row in distinct_cities_rows if row[0]]

    include_stats = mine or is_admin
    return (
        jsonify(
            {
                "events": [e.to_dict(include_stats=include_stats) for e in events],
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                },
                "available_cities": cities,
            }
        ),
        200,
    )


@events_bp.route("/<int:event_id>", methods=["GET"])
def get_event(event_id: int):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found."}), 404

    can_manage = _can_manage_event(current_user, event)
    if event.status != "PUBLISHED" and not can_manage:
        return jsonify({"error": "You do not have permission to view this non-published event."}), 403

    event_data = event.to_dict(include_stats=can_manage)
    my_registration = None
    if current_user.is_authenticated and current_user.active:
        reg = Registration.query.filter_by(
            attendee_id=current_user.id,
            event_id=event.id,
        ).first()
        if reg:
            my_registration = reg.to_dict(include_event=False, include_attendee=False)

    return (
        jsonify(
            {
                "event": event_data,
                "my_registration": my_registration,
                "can_manage": can_manage,
            }
        ),
        200,
    )


@events_bp.route("", methods=["POST"])
@roles_required_json("organizer", "admin")
def create_event():
    data = request.get_json(silent=True) or {}
    cleaned, error = validate_event_payload(data, partial=False)
    if error:
        return jsonify({"error": error}), 400

    category = db.session.get(Category, cleaned["category_id"])
    if not category:
        return jsonify({"error": "Selected category does not exist."}), 404

    try:
        event = Event(
            title=cleaned["title"],
            description=cleaned["description"],
            category_id=cleaned["category_id"],
            organizer_id=current_user.id,
            venue=cleaned["venue"],
            city=cleaned["city"],
            start_datetime=cleaned["start_datetime"],
            end_datetime=cleaned["end_datetime"],
            registration_deadline=cleaned["registration_deadline"],
            capacity=cleaned["capacity"],
            registered_count=0,
            price=cleaned["price"],
            status=cleaned["status"],
            moderation_notes=cleaned.get("moderation_notes"),
        )
        db.session.add(event)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Event created successfully.",
                    "event": event.to_dict(include_stats=True),
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to create event: {str(exc)}"}), 500


@events_bp.route("/<int:event_id>", methods=["PUT"])
@roles_required_json("organizer", "admin")
def update_event(event_id: int):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found."}), 404

    if not _can_manage_event(current_user, event):
        return jsonify({"error": "You are only authorized to modify events you created."}), 403

    data = request.get_json(silent=True) or {}
    cleaned, error = validate_event_payload(data, partial=True, existing_event=event)
    if error:
        return jsonify({"error": error}), 400

    if "category_id" in cleaned:
        category = db.session.get(Category, cleaned["category_id"])
        if not category:
            return jsonify({"error": "Selected category does not exist."}), 404

    for key, value in cleaned.items():
        setattr(event, key, value)

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Event updated successfully.",
                    "event": event.to_dict(include_stats=True),
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to update event: {str(exc)}"}), 500


@events_bp.route("/<int:event_id>", methods=["DELETE"])
@roles_required_json("organizer", "admin")
def delete_or_cancel_event(event_id: int):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found."}), 404

    if not _can_manage_event(current_user, event):
        return jsonify({"error": "You are only authorized to delete or cancel events you created."}), 403

    total_registrations = Registration.query.filter_by(event_id=event.id).count()

    # Draft events with zero registrations can be permanently deleted
    if event.status == "DRAFT" and total_registrations == 0:
        db.session.delete(event)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Draft event permanently deleted.",
                    "action": "DELETED",
                }
            ),
            200,
        )

    # Published events or events with registration records are transitioned to CANCELLED
    # so attendee registration history is preserved intact.
    event.status = "CANCELLED"
    db.session.commit()
    return (
        jsonify(
            {
                "message": "Event transitioned to CANCELLED to preserve registration history.",
                "action": "CANCELLED",
                "event": event.to_dict(include_stats=True),
            }
        ),
        200,
    )
