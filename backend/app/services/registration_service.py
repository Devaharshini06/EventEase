from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from ..models import db, Event, Registration, User, Notification
from ..models.registration import generate_registration_reference
from ..tasks.reminder_tasks import enqueue_registration_confirmation


def register_attendee_for_event(
    event_id: int,
    user: User,
    notes: Optional[str] = None,
) -> Tuple[Optional[Registration], Optional[str], int]:
    """
    Transaction-safe event registration with atomic conditional capacity update.
    Returns (Registration | None, error_message | None, http_status_code).
    """
    if not user or not user.is_authenticated:
        return None, "Authentication required.", 401

    if not user.active:
        return None, "Account is deactivated and cannot register for events.", 403

    event = db.session.get(Event, event_id)
    if not event:
        return None, "Event not found.", 404

    if event.status != "PUBLISHED":
        return None, "Registrations are only accepted for published events.", 400

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if event.end_datetime <= now:
        return None, "Cannot register for an event that has already ended.", 400

    if event.registration_deadline <= now:
        return None, "The registration deadline for this event has passed.", 400

    existing = Registration.query.filter_by(
        attendee_id=user.id,
        event_id=event.id,
    ).first()

    if existing and existing.status in ("CONFIRMED", "CHECKED_IN"):
        return None, "You already have an active registration for this event.", 409

    try:
        # Atomic conditional update at the database level:
        # Only increments registered_count if status is PUBLISHED and registered_count < capacity.
        stmt = (
            update(Event)
            .where(
                Event.id == event_id,
                Event.status == "PUBLISHED",
                Event.registered_count < Event.capacity,
            )
            .values(registered_count=Event.registered_count + 1)
        )
        result = db.session.execute(stmt)
        if result.rowcount == 0:
            db.session.rollback()
            return None, "Event has reached maximum attendee capacity.", 409

        if existing and existing.status == "CANCELLED":
            existing.status = "CONFIRMED"
            existing.registered_at = now
            existing.cancelled_at = None
            existing.checked_in_at = None
            existing.registration_reference = generate_registration_reference()
            if notes is not None:
                existing.notes = str(notes).strip()[:500]
            registration = existing
        else:
            registration = Registration(
                attendee_id=user.id,
                event_id=event.id,
                registration_reference=generate_registration_reference(),
                status="CONFIRMED",
                notes=str(notes).strip()[:500] if notes else None,
                registered_at=now,
            )
            db.session.add(registration)

        notification = Notification(
            recipient_id=user.id,
            title=f"Registration Confirmed: {event.title}",
            content=(
                f"Your seat for '{event.title}' at {event.venue}, {event.city} is confirmed. "
                f"Reference: {registration.registration_reference}"
            ),
            notification_type="REGISTRATION_CONFIRMED",
        )
        db.session.add(notification)

        db.session.commit()
        db.session.refresh(registration)
        db.session.refresh(event)

        enqueue_registration_confirmation(registration.id)
        return registration, None, 201

    except IntegrityError:
        db.session.rollback()
        return None, "You already have an active registration for this event or a concurrency conflict occurred.", 409
    except Exception as exc:
        db.session.rollback()
        return None, f"Registration failed due to an unexpected error: {str(exc)}", 500


def cancel_registration(
    registration_id: int,
    acting_user: User,
) -> Tuple[Optional[Registration], Optional[str], int]:
    """
    Cancels an eligible registration and atomically releases capacity.
    Authorized for:
    - The registered attendee themselves (before event ends and if not checked in)
    - The event organizer
    - An administrator
    """
    registration = db.session.get(Registration, registration_id)
    if not registration:
        return None, "Registration not found.", 404

    event = registration.event
    is_admin = acting_user.has_role_name("admin")
    is_event_organizer = (
        acting_user.has_role_name("organizer") and event and event.organizer_id == acting_user.id
    )
    is_owner = registration.attendee_id == acting_user.id

    if not (is_admin or is_event_organizer or is_owner):
        return None, "You do not have permission to cancel this registration.", 403

    if registration.status == "CANCELLED":
        return None, "Registration is already cancelled.", 400

    if registration.status == "CHECKED_IN" and not (is_admin or is_event_organizer):
        return None, "Checked-in registrations cannot be self-cancelled.", 400

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if is_owner and not (is_admin or is_event_organizer):
        if event and event.end_datetime <= now:
            return None, "Cannot cancel registration for an event that has already ended.", 400

    try:
        stmt = (
            update(Event)
            .where(Event.id == registration.event_id, Event.registered_count > 0)
            .values(registered_count=Event.registered_count - 1)
        )
        db.session.execute(stmt)

        registration.status = "CANCELLED"
        registration.cancelled_at = now

        notification = Notification(
            recipient_id=registration.attendee_id,
            title=f"Registration Cancelled: {event.title if event else 'Event'}",
            content=f"Registration {registration.registration_reference} has been marked as cancelled.",
            notification_type="REGISTRATION_CANCELLED",
        )
        db.session.add(notification)

        db.session.commit()
        db.session.refresh(registration)
        return registration, None, 200
    except Exception as exc:
        db.session.rollback()
        return None, f"Could not cancel registration: {str(exc)}", 500


def check_in_registration(
    acting_user: User,
    registration_id: Optional[int] = None,
    registration_reference: Optional[str] = None,
    event_id: Optional[int] = None,
) -> Tuple[Optional[Registration], Optional[str], int]:
    """
    Organizer or Admin checks in an attendee by registration_id or registration_reference.
    """
    registration = None
    if registration_id is not None:
        registration = db.session.get(Registration, registration_id)
    elif registration_reference:
        query = Registration.query.filter_by(
            registration_reference=registration_reference.strip().upper()
        )
        if event_id is not None:
            query = query.filter_by(event_id=event_id)
        registration = query.first()

    if not registration:
        return None, "Registration record not found for check-in.", 404

    event = registration.event
    if event_id is not None and registration.event_id != int(event_id):
        return None, "Registration reference does not belong to this event.", 400

    is_admin = acting_user.has_role_name("admin")
    is_event_organizer = (
        acting_user.has_role_name("organizer") and event and event.organizer_id == acting_user.id
    )

    if not (is_admin or is_event_organizer):
        return None, "Only the event organizer or an administrator can perform check-ins.", 403

    if event.status == "CANCELLED":
        return None, "Cannot check in attendees for a cancelled event.", 400

    if registration.status == "CANCELLED":
        return None, "Cannot check in a cancelled registration.", 400

    if registration.status == "CHECKED_IN" or registration.checked_in_at is not None:
        return None, "Attendee has already been checked in.", 409

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        registration.status = "CHECKED_IN"
        registration.checked_in_at = now

        notification = Notification(
            recipient_id=registration.attendee_id,
            title=f"Checked In: {event.title}",
            content=f"Check-in verified for {event.title} (Reference: {registration.registration_reference}).",
            notification_type="CHECK_IN",
        )
        db.session.add(notification)

        db.session.commit()
        db.session.refresh(registration)
        return registration, None, 200
    except Exception as exc:
        db.session.rollback()
        return None, f"Check-in failed: {str(exc)}", 500
