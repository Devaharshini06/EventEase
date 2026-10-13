from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user, login_user, logout_user
from flask_security.utils import hash_password, verify_password
from sqlalchemy.exc import IntegrityError
from ..models import db, User, Role, Notification
from ..schemas import validate_email_format
from . import token_auth_required

auth_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")

ALLOWED_PUBLIC_ROLES = {"attendee", "organizer"}


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    full_name = str(data.get("full_name", "")).strip()
    organization = str(data.get("organization", "")).strip()
    phone = str(data.get("phone", "")).strip()
    requested_role = str(data.get("role", "attendee")).strip().lower()

    if not email or not validate_email_format(email):
        return jsonify({"error": "Please provide a valid email address."}), 400

    if not full_name or len(full_name) < 2 or len(full_name) > 150:
        return jsonify({"error": "Full name is required (2 to 150 characters)."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    # Strictly forbid public self-assignment of admin or unknown roles
    if requested_role not in ALLOWED_PUBLIC_ROLES:
        return (
            jsonify(
                {
                    "error": "Invalid role selection. Public registration only permits 'attendee' or 'organizer'."
                }
            ),
            403,
        )

    existing_user = User.query.filter(db.func.lower(User.email) == email).first()
    if existing_user:
        return jsonify({"error": "An account with this email address already exists."}), 409

    user_datastore = current_app.extensions["security"].datastore
    try:
        role_obj = Role.query.filter_by(name=requested_role).first()
        if not role_obj:
            role_obj = user_datastore.find_or_create_role(name=requested_role)

        user = user_datastore.create_user(
            email=email,
            password=hash_password(password),
            full_name=full_name,
            organization=organization[:150] if organization else None,
            phone=phone[:40] if phone else None,
            active=True,
        )
        user_datastore.add_role_to_user(user, role_obj)
        db.session.flush()

        welcome_note = Notification(
            recipient_id=user.id,
            title="Welcome to EventEase",
            content=f"Your {requested_role} account has been created and is ready for use.",
            notification_type="WELCOME",
        )
        db.session.add(welcome_note)
        db.session.commit()

        token = user.get_auth_token()

        return (
            jsonify(
                {
                    "message": "Registration successful.",
                    "token": token,
                    "user": user.to_dict(),
                }
            ),
            201,
        )
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "An account with this email address already exists."}), 409
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Registration could not be completed: {str(exc)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if not user or not verify_password(password, user.password):
        return jsonify({"error": "Invalid email or password."}), 401

    if not user.active:
        return (
            jsonify(
                {
                    "error": "This account has been deactivated by an administrator. Please contact platform support."
                }
            ),
            403,
        )

    token = user.get_auth_token()

    return (
        jsonify(
            {
                "message": "Login successful.",
                "token": token,
                "user": user.to_dict(),
            }
        ),
        200,
    )


@auth_bp.route("/me", methods=["GET"])
@token_auth_required
def get_me():
    unread_count = Notification.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).count()
    user_data = current_user.to_dict()
    user_data["unread_notifications_count"] = unread_count
    return jsonify({"user": user_data}), 200


@auth_bp.route("/profile", methods=["PUT"])
@token_auth_required
def update_profile():
    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        full_name = str(data["full_name"]).strip()
        if len(full_name) < 2 or len(full_name) > 150:
            return jsonify({"error": "Full name must be between 2 and 150 characters."}), 400
        current_user.full_name = full_name

    if "organization" in data:
        current_user.organization = str(data["organization"]).strip()[:150]

    if "phone" in data:
        current_user.phone = str(data["phone"]).strip()[:40]

    if "bio" in data:
        current_user.bio = str(data["bio"]).strip()[:1000]

    if data.get("new_password"):
        current_password = str(data.get("current_password", ""))
        new_password = str(data.get("new_password", ""))
        if not current_password or not verify_password(current_password, current_user.password):
            return jsonify({"error": "Current password is incorrect."}), 400
        if len(new_password) < 8:
            return jsonify({"error": "New password must be at least 8 characters long."}), 400
        current_user.password = hash_password(new_password)

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Profile updated successfully.",
                    "user": current_user.to_dict(),
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to update profile: {str(exc)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
@token_auth_required
def logout():
    try:
        user = db.session.get(User, current_user.id)
        if user:
            user.rotate_uniquifier()
            db.session.commit()
        logout_user()
        return jsonify({"message": "Logged out successfully."}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Logout error: {str(exc)}"}), 500


@auth_bp.route("/notifications", methods=["GET"])
@token_auth_required
def get_notifications():
    notifications = (
        Notification.query.filter_by(recipient_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    return (
        jsonify(
            {
                "notifications": [n.to_dict() for n in notifications],
                "unread_count": sum(1 for n in notifications if not n.is_read),
            }
        ),
        200,
    )


@auth_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@token_auth_required
def mark_notification_read(notification_id: int):
    notification = db.session.get(Notification, notification_id)
    if not notification or notification.recipient_id != current_user.id:
        return jsonify({"error": "Notification not found."}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify({"notification": notification.to_dict()}), 200
