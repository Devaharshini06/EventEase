from datetime import datetime, timezone
from . import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer(), primary_key=True)
    recipient_id = db.Column(
        db.Integer(),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, default="INFO")
    is_read = db.Column(db.Boolean(), nullable=False, default=False, index=True)
    created_at = db.Column(
        db.DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    recipient = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "title": self.title,
            "content": self.content,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
