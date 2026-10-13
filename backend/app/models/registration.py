import secrets
import string
from datetime import datetime, timezone
from . import db


def generate_registration_reference() -> str:
    alphabet = string.ascii_uppercase + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"EVT-{token[:4]}-{token[4:]}"


class Registration(db.Model):
    __tablename__ = "registrations"

    id = db.Column(db.Integer(), primary_key=True)
    attendee_id = db.Column(
        db.Integer(),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = db.Column(
        db.Integer(),
        db.ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    registration_reference = db.Column(
        db.String(32),
        unique=True,
        nullable=False,
        index=True,
        default=generate_registration_reference,
    )
    status = db.Column(
        db.String(32),
        nullable=False,
        default="CONFIRMED",
        index=True,
    )  # CONFIRMED, CHECKED_IN, CANCELLED
    notes = db.Column(db.String(500), nullable=True)
    registered_at = db.Column(
        db.DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    checked_in_at = db.Column(db.DateTime(), nullable=True)
    cancelled_at = db.Column(db.DateTime(), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("attendee_id", "event_id", name="uq_attendee_event_registration"),
        db.CheckConstraint(
            "status IN ('CONFIRMED', 'CHECKED_IN', 'CANCELLED')",
            name="ck_registration_valid_status",
        ),
    )

    attendee = db.relationship("User", back_populates="registrations", lazy="joined")
    event = db.relationship("Event", back_populates="registrations", lazy="joined")

    def to_dict(self, include_event: bool = True, include_attendee: bool = True):
        data = {
            "id": self.id,
            "attendee_id": self.attendee_id,
            "event_id": self.event_id,
            "registration_reference": self.registration_reference,
            "status": self.status,
            "notes": self.notes or "",
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "checked_in_at": self.checked_in_at.isoformat() if self.checked_in_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
        if include_attendee and self.attendee:
            data["attendee"] = {
                "id": self.attendee.id,
                "full_name": self.attendee.full_name,
                "email": self.attendee.email,
                "organization": self.attendee.organization or "",
                "phone": self.attendee.phone or "",
            }
        if include_event and self.event:
            data["event"] = self.event.to_dict(include_stats=False)
        return data
