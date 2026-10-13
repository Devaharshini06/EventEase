import re
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email_format(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def validate_event_payload(
    data: Dict[str, Any],
    partial: bool = False,
    existing_event: Any = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(data, dict):
        return None, "Invalid JSON payload."

    required_fields = [
        "title",
        "description",
        "category_id",
        "venue",
        "city",
        "start_datetime",
        "end_datetime",
        "registration_deadline",
        "capacity",
    ]
    if not partial:
        missing = [f for f in required_fields if f not in data or data.get(f) in (None, "")]
        if missing:
            return None, f"Missing required fields: {', '.join(missing)}"

    cleaned: Dict[str, Any] = {}

    if "title" in data:
        title = str(data["title"]).strip()
        if len(title) < 3 or len(title) > 200:
            return None, "Event title must be between 3 and 200 characters."
        cleaned["title"] = title

    if "description" in data:
        description = str(data["description"]).strip()
        if len(description) < 10:
            return None, "Event description must be at least 10 characters."
        cleaned["description"] = description

    if "category_id" in data:
        try:
            cleaned["category_id"] = int(data["category_id"])
        except (ValueError, TypeError):
            return None, "Category ID must be a valid integer."

    if "venue" in data:
        venue = str(data["venue"]).strip()
        if not venue or len(venue) > 255:
            return None, "Venue is required and must be under 255 characters."
        cleaned["venue"] = venue

    if "city" in data:
        city = str(data["city"]).strip()
        if not city or len(city) > 100:
            return None, "City is required and must be under 100 characters."
        cleaned["city"] = city

    if "capacity" in data:
        try:
            capacity = int(data["capacity"])
        except (ValueError, TypeError):
            return None, "Capacity must be a valid integer."
        if capacity <= 0 or capacity > 100000:
            return None, "Capacity must be a positive integer between 1 and 100,000."
        if existing_event is not None and capacity < existing_event.registered_count:
            return (
                None,
                f"Capacity cannot be reduced below current active registrations ({existing_event.registered_count}).",
            )
        cleaned["capacity"] = capacity

    if "price" in data and data["price"] is not None and data["price"] != "":
        try:
            price = float(data["price"])
        except (ValueError, TypeError):
            return None, "Price must be a valid number."
        if price < 0 or price > 100000:
            return None, "Price must be between 0 and 100,000."
        cleaned["price"] = round(price, 2)
    elif not partial:
        cleaned["price"] = 0.0

    if "status" in data and data["status"] is not None:
        status = str(data["status"]).strip().upper()
        if status not in ("DRAFT", "PUBLISHED", "CANCELLED", "ARCHIVED"):
            return None, "Status must be one of DRAFT, PUBLISHED, CANCELLED, ARCHIVED."
        cleaned["status"] = status
    elif not partial:
        cleaned["status"] = "DRAFT"

    if "moderation_notes" in data and data["moderation_notes"] is not None:
        cleaned["moderation_notes"] = str(data["moderation_notes"]).strip()[:500]

    start_dt = (
        parse_iso_datetime(data["start_datetime"])
        if "start_datetime" in data
        else (existing_event.start_datetime if existing_event else None)
    )
    end_dt = (
        parse_iso_datetime(data["end_datetime"])
        if "end_datetime" in data
        else (existing_event.end_datetime if existing_event else None)
    )
    deadline_dt = (
        parse_iso_datetime(data["registration_deadline"])
        if "registration_deadline" in data
        else (existing_event.registration_deadline if existing_event else None)
    )

    if "start_datetime" in data and start_dt is None:
        return None, "Invalid start_datetime format. Use ISO-8601 format."
    if "end_datetime" in data and end_dt is None:
        return None, "Invalid end_datetime format. Use ISO-8601 format."
    if "registration_deadline" in data and deadline_dt is None:
        return None, "Invalid registration_deadline format. Use ISO-8601 format."

    if start_dt and end_dt:
        if end_dt <= start_dt:
            return None, "Event end date/time must be after start date/time."
    if start_dt and deadline_dt:
        if deadline_dt > end_dt if end_dt else False:
            return None, "Registration deadline cannot be after event end date/time."
        if deadline_dt > start_dt:
            return None, "Registration deadline must be on or before the event start date/time."

    if "start_datetime" in data:
        cleaned["start_datetime"] = start_dt
    if "end_datetime" in data:
        cleaned["end_datetime"] = end_dt
    if "registration_deadline" in data:
        cleaned["registration_deadline"] = deadline_dt

    return cleaned, None
