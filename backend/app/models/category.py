from datetime import datetime, timezone
from . import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    events = db.relationship("Event", back_populates="category", lazy="dynamic")

    def to_dict(self, include_counts: bool = False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_counts:
            data["event_count"] = self.events.count()
            data["published_event_count"] = self.events.filter_by(status="PUBLISHED").count()
        return data
