from datetime import datetime, timezone
from . import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text(), nullable=False)
    category_id = db.Column(
        db.Integer(),
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organizer_id = db.Column(
        db.Integer(),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    venue = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    start_datetime = db.Column(db.DateTime(), nullable=False, index=True)
    end_datetime = db.Column(db.DateTime(), nullable=False)
    registration_deadline = db.Column(db.DateTime(), nullable=False, index=True)
    capacity = db.Column(db.Integer(), nullable=False)
    registered_count = db.Column(db.Integer(), nullable=False, default=0)
    price = db.Column(db.Float(), nullable=False, default=0.0)
    status = db.Column(
        db.String(32),
        nullable=False,
        default="DRAFT",
        index=True,
    )  # DRAFT, PUBLISHED, CANCELLED, ARCHIVED
    moderation_notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    updated_at = db.Column(
        db.DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    __table_args__ = (
        db.CheckConstraint("capacity > 0", name="ck_event_positive_capacity"),
        db.CheckConstraint(
            "registered_count >= 0 AND registered_count <= capacity",
            name="ck_event_capacity_bounds",
        ),
        db.CheckConstraint("price >= 0", name="ck_event_non_negative_price"),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'CANCELLED', 'ARCHIVED')",
            name="ck_event_valid_status",
        ),
    )

    category = db.relationship("Category", back_populates="events", lazy="joined")
    organizer = db.relationship("User", back_populates="organized_events", lazy="joined")
    registrations = db.relationship(
        "Registration",
        back_populates="event",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def remaining_capacity(self) -> int:
        return max(0, self.capacity - self.registered_count)

    @property
    def is_registration_open(self) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (
            self.status == "PUBLISHED"
            and self.remaining_capacity > 0
            and self.registration_deadline > now
            and self.end_datetime > now
        )

    def to_dict(self, include_stats: bool = False):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "Uncategorized",
            "organizer_id": self.organizer_id,
            "organizer_name": self.organizer.full_name if self.organizer else "Unknown",
            "organizer_organization": (
                self.organizer.organization if self.organizer and self.organizer.organization else ""
            ),
            "venue": self.venue,
            "city": self.city,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "registration_deadline": (
                self.registration_deadline.isoformat() if self.registration_deadline else None
            ),
            "capacity": self.capacity,
            "registered_count": self.registered_count,
            "remaining_capacity": self.remaining_capacity,
            "price": round(float(self.price or 0.0), 2),
            "is_free": float(self.price or 0.0) == 0.0,
            "status": self.status,
            "moderation_notes": self.moderation_notes or "",
            "is_registration_open": self.is_registration_open,
            "is_past": self.end_datetime <= now if self.end_datetime else False,
            "deadline_passed": (
                self.registration_deadline <= now if self.registration_deadline else False
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_stats:
            confirmed = self.registrations.filter(
                db.or_(
                    db.column("status") == "CONFIRMED",
                    db.column("status") == "CHECKED_IN",
                )
            ).count()
            checked_in = self.registrations.filter_by(status="CHECKED_IN").count()
            cancelled = self.registrations.filter_by(status="CANCELLED").count()
            data["stats"] = {
                "active_registrations": confirmed,
                "checked_in_count": checked_in,
                "cancelled_count": cancelled,
                "remaining_capacity": self.remaining_capacity,
                "occupancy_percent": (
                    round((self.registered_count / self.capacity) * 100, 1)
                    if self.capacity > 0
                    else 0.0
                ),
            }
        return data
