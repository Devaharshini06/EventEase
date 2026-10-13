from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_security import current_user
from sqlalchemy import func
from ..models import db, User, Event, Category, Registration
from . import token_auth_required, roles_required_json

dashboards_bp = Blueprint("dashboards_api", __name__, url_prefix="/api/dashboard")


@dashboards_bp.route("/attendee", methods=["GET"])
@token_auth_required
def attendee_dashboard():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    registrations = (
        Registration.query.filter_by(attendee_id=current_user.id)
        .order_by(Registration.registered_at.desc())
        .all()
    )

    upcoming = []
    past = []
    cancelled = []
    checked_in_count = 0

    for reg in registrations:
        reg_dict = reg.to_dict(include_event=True, include_attendee=False)
        if reg.status == "CHECKED_IN":
            checked_in_count += 1

        if reg.status == "CANCELLED":
            cancelled.append(reg_dict)
        elif reg.event and reg.event.end_datetime > now:
            upcoming.append(reg_dict)
        else:
            past.append(reg_dict)

    return (
        jsonify(
            {
                "metrics": {
                    "total_registrations": len(registrations),
                    "upcoming_events_count": len(upcoming),
                    "past_events_count": len(past),
                    "cancelled_registrations_count": len(cancelled),
                    "checked_in_count": checked_in_count,
                },
                "upcoming_registrations": upcoming,
                "past_registrations": past,
                "cancelled_registrations": cancelled,
                "registration_history": [
                    r.to_dict(include_event=True, include_attendee=False) for r in registrations
                ],
            }
        ),
        200,
    )


@dashboards_bp.route("/organizer", methods=["GET"])
@roles_required_json("organizer", "admin")
def organizer_dashboard():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    is_admin = current_user.has_role_name("admin")
    scope = request.args.get("scope", "own")

    query = Event.query
    if not is_admin or scope == "own":
        query = query.filter_by(organizer_id=current_user.id)

    events = query.order_by(Event.start_datetime.asc()).all()

    total_events = len(events)
    published_events = sum(1 for e in events if e.status == "PUBLISHED")
    draft_events = sum(1 for e in events if e.status == "DRAFT")
    cancelled_events = sum(1 for e in events if e.status in ("CANCELLED", "ARCHIVED"))
    total_active_registrations = sum(e.registered_count for e in events)
    total_capacity = sum(e.capacity for e in events if e.status == "PUBLISHED")
    remaining_capacity = sum(e.remaining_capacity for e in events if e.status == "PUBLISHED")

    event_ids = [e.id for e in events]
    checked_in_total = 0
    if event_ids:
        checked_in_total = (
            Registration.query.filter(
                Registration.event_id.in_(event_ids),
                Registration.status == "CHECKED_IN",
            ).count()
        )

    upcoming_events = [
        e.to_dict(include_stats=True) for e in events if e.end_datetime > now and e.status != "CANCELLED"
    ]
    past_events = [
        e.to_dict(include_stats=True) for e in events if e.end_datetime <= now
    ]
    event_breakdown = [
        {
            "event_id": e.id,
            "title": e.title,
            "status": e.status,
            "category_name": e.category.name if e.category else "",
            "start_datetime": e.start_datetime.isoformat() if e.start_datetime else None,
            "capacity": e.capacity,
            "registered_count": e.registered_count,
            "remaining_capacity": e.remaining_capacity,
            "occupancy_percent": (
                round((e.registered_count / e.capacity) * 100, 1) if e.capacity > 0 else 0.0
            ),
        }
        for e in events
    ]

    return (
        jsonify(
            {
                "metrics": {
                    "total_events": total_events,
                    "published_events": published_events,
                    "draft_events": draft_events,
                    "cancelled_events": cancelled_events,
                    "total_active_registrations": total_active_registrations,
                    "total_checked_in": checked_in_total,
                    "total_published_capacity": total_capacity,
                    "remaining_published_capacity": remaining_capacity,
                },
                "event_breakdown": event_breakdown,
                "upcoming_events": upcoming_events,
                "past_events": past_events,
            }
        ),
        200,
    )


@dashboards_bp.route("/admin", methods=["GET"])
@roles_required_json("admin")
def admin_dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    inactive_users = total_users - active_users

    total_events = Event.query.count()
    published_events = Event.query.filter_by(status="PUBLISHED").count()
    draft_events = Event.query.filter_by(status="DRAFT").count()
    cancelled_events = Event.query.filter_by(status="CANCELLED").count()

    total_registrations = Registration.query.count()
    active_registrations = Registration.query.filter(
        Registration.status.in_(["CONFIRMED", "CHECKED_IN"])
    ).count()
    checked_in_registrations = Registration.query.filter_by(status="CHECKED_IN").count()
    cancelled_registrations = Registration.query.filter_by(status="CANCELLED").count()

    # Events grouped by category via SQLAlchemy query
    category_rows = (
        db.session.query(
            Category.id,
            Category.name,
            func.count(Event.id).label("event_count"),
            func.coalesce(func.sum(Event.registered_count), 0).label("active_registrations"),
            func.coalesce(func.sum(Event.capacity), 0).label("total_capacity"),
        )
        .outerjoin(Event, Event.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(func.count(Event.id).desc(), Category.name.asc())
        .all()
    )

    events_by_category = [
        {
            "category_id": row.id,
            "category_name": row.name,
            "event_count": int(row.event_count or 0),
            "active_registrations": int(row.active_registrations or 0),
            "total_capacity": int(row.total_capacity or 0),
        }
        for row in category_rows
    ]

    # Recent registrations for platform activity feed
    recent_regs = (
        Registration.query.order_by(Registration.registered_at.desc()).limit(10).all()
    )
    recent_activity = [
        {
            "id": r.id,
            "registration_reference": r.registration_reference,
            "status": r.status,
            "registered_at": r.registered_at.isoformat() if r.registered_at else None,
            "attendee_name": r.attendee.full_name if r.attendee else "Unknown",
            "attendee_email": r.attendee.email if r.attendee else "",
            "event_id": r.event_id,
            "event_title": r.event.title if r.event else "Unknown Event",
        }
        for r in recent_regs
    ]

    all_events = Event.query.order_by(Event.created_at.desc()).limit(15).all()

    return (
        jsonify(
            {
                "metrics": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "inactive_users": inactive_users,
                    "total_events": total_events,
                    "published_events": published_events,
                    "draft_events": draft_events,
                    "cancelled_events": cancelled_events,
                    "total_registrations": total_registrations,
                    "active_registrations": active_registrations,
                    "checked_in_registrations": checked_in_registrations,
                    "cancelled_registrations": cancelled_registrations,
                },
                "events_by_category": events_by_category,
                "recent_activity": recent_activity,
                "recent_events": [e.to_dict(include_stats=True) for e in all_events],
            }
        ),
        200,
    )
