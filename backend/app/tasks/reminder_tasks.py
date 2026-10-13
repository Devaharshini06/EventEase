import os
from datetime import datetime, timedelta, timezone

try:
    from celery import Celery
except ImportError:
    Celery = None

celery_app = None
if Celery is not None:
    broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    celery_app = Celery("eventease_tasks", broker=broker_url, backend=result_backend)
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )


def enqueue_registration_confirmation(registration_id: int) -> bool:
    """
    Queues a background confirmation task if CELERY_ENABLED=true and Redis is reachable.
    Otherwise falls back gracefully so the main application works without Redis/Celery.
    """
    if os.environ.get("CELERY_ENABLED", "false").lower() != "true" or celery_app is None:
        return False
    try:
        send_registration_confirmation_task.delay(registration_id)
        return True
    except Exception:
        return False


def process_upcoming_event_reminders() -> int:
    """
    Creates in-app reminder notifications for attendees registered for events starting within 48 hours.
    Can be invoked directly or scheduled via Celery Beat.
    """
    from ..models import db, Event, Registration, Notification

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_end = now + timedelta(hours=48)

    upcoming_events = Event.query.filter(
        Event.status == "PUBLISHED",
        Event.start_datetime > now,
        Event.start_datetime <= window_end,
    ).all()

    created_count = 0
    for event in upcoming_events:
        active_regs = Registration.query.filter_by(
            event_id=event.id, status="CONFIRMED"
        ).all()
        for reg in active_regs:
            title = f"Upcoming Event Reminder: {event.title}"
            already_sent = Notification.query.filter_by(
                recipient_id=reg.attendee_id,
                title=title,
            ).first()
            if not already_sent:
                db.session.add(
                    Notification(
                        recipient_id=reg.attendee_id,
                        title=title,
                        content=(
                            f"Reminder: '{event.title}' starts at {event.start_datetime.strftime('%Y-%m-%d %H:%M UTC')} "
                            f"at {event.venue}, {event.city}. Pass reference: {reg.registration_reference}"
                        ),
                        notification_type="EVENT_REMINDER",
                    )
                )
                created_count += 1
    if created_count > 0:
        db.session.commit()
    return created_count


def generate_daily_organizer_summary() -> int:
    """
    Generates daily registration summary notifications for active organizers.
    """
    from ..models import db, Event, Notification

    events = Event.query.filter_by(status="PUBLISHED").all()
    organizer_totals = {}
    for ev in events:
        organizer_totals.setdefault(ev.organizer_id, {"events": 0, "registrations": 0})
        organizer_totals[ev.organizer_id]["events"] += 1
        organizer_totals[ev.organizer_id]["registrations"] += ev.registered_count

    count = 0
    for organizer_id, stats in organizer_totals.items():
        db.session.add(
            Notification(
                recipient_id=organizer_id,
                title="Daily Organizer Activity Summary",
                content=(
                    f"You have {stats['events']} published event(s) with "
                    f"{stats['registrations']} total active registration(s)."
                ),
                notification_type="ORGANIZER_SUMMARY",
            )
        )
        count += 1
    if count > 0:
        db.session.commit()
    return count


if celery_app is not None:
    @celery_app.task(name="eventease.send_registration_confirmation")
    def send_registration_confirmation_task(registration_id: int):
        return {"registration_id": registration_id, "status": "processed_in_app"}

    @celery_app.task(name="eventease.process_upcoming_event_reminders")
    def process_upcoming_event_reminders_task():
        return {"reminders_created": process_upcoming_event_reminders()}
