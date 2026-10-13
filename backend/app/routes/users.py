from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user
from sqlalchemy import or_
from ..models import db, User, Role
from . import roles_required_json

users_bp = Blueprint("users_api", __name__, url_prefix="/api/users")


@users_bp.route("", methods=["GET"])
@roles_required_json("admin")
def list_users():
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role", "").strip().lower()
    active_filter = request.args.get("active", "").strip().lower()

    query = User.query

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                User.organization.ilike(pattern),
            )
        )

    if active_filter == "true":
        query = query.filter(User.active.is_(True))
    elif active_filter == "false":
        query = query.filter(User.active.is_(False))

    users = query.order_by(User.created_at.desc()).all()
    if role_filter and role_filter != "all":
        users = [u for u in users if u.has_role_name(role_filter)]

    return (
        jsonify(
            {
                "users": [u.to_dict() for u in users],
                "total": len(users),
            }
        ),
        200,
    )


@users_bp.route("/<int:user_id>/status", methods=["PUT"])
@roles_required_json("admin")
def update_user_status(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    if "active" not in data or not isinstance(data["active"], bool):
        return jsonify({"error": "Boolean 'active' field is required."}), 400

    new_active = data["active"]
    if user.id == current_user.id and not new_active:
        return jsonify({"error": "Administrators cannot deactivate their own account."}), 400

    user.active = new_active
    if not new_active:
        # Immediately invalidate any existing Authentication-Token for the deactivated user
        user.rotate_uniquifier()

    db.session.commit()
    return (
        jsonify(
            {
                "message": f"User account {'activated' if new_active else 'deactivated'} successfully.",
                "user": user.to_dict(),
            }
        ),
        200,
    )


@users_bp.route("/<int:user_id>/role", methods=["PUT"])
@roles_required_json("admin")
def update_user_role(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    role_name = str(data.get("role", "")).strip().lower()
    if role_name not in ("attendee", "organizer", "admin"):
        return jsonify({"error": "Role must be one of 'attendee', 'organizer', or 'admin'."}), 400

    if user.id == current_user.id and role_name != "admin":
        return jsonify({"error": "Administrators cannot remove their own admin role."}), 400

    user_datastore = current_app.extensions["security"].datastore
    role_obj = Role.query.filter_by(name=role_name).first()
    if not role_obj:
        role_obj = user_datastore.find_or_create_role(name=role_name)

    user.roles = [role_obj]
    db.session.commit()

    return (
        jsonify(
            {
                "message": f"User role updated to '{role_name}'.",
                "user": user.to_dict(),
            }
        ),
        200,
    )
