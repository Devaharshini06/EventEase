import uuid
from datetime import datetime, timezone
from flask_security import UserMixin, RoleMixin
from . import db

roles_users = db.Table(
    "roles_users",
    db.Column("id", db.Integer(), primary_key=True),
    db.Column("user_id", db.Integer(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    db.Column("role_id", db.Integer(), db.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    db.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
)


class Role(db.Model, RoleMixin):
    __tablename__ = "roles"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    organization = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    bio = db.Column(db.Text(), nullable=True)
    active = db.Column(db.Boolean(), nullable=False, default=True, index=True)
    fs_uniquifier = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
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

    roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
        lazy="joined",
    )
    organized_events = db.relationship(
        "Event",
        back_populates="organizer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    registrations = db.relationship(
        "Registration",
        back_populates="attendee",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="recipient",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def primary_role(self) -> str:
        role_names = [r.name for r in self.roles]
        if "admin" in role_names:
            return "admin"
        if "organizer" in role_names:
            return "organizer"
        return "attendee"

    def has_role_name(self, role_name: str) -> bool:
        return any(r.name == role_name for r in self.roles)

    def rotate_uniquifier(self):
        self.fs_uniquifier = uuid.uuid4().hex

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "organization": self.organization or "",
            "phone": self.phone or "",
            "bio": self.bio or "",
            "active": self.active,
            "roles": [r.name for r in self.roles],
            "primary_role": self.primary_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
