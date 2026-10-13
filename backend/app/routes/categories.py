from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from ..models import db, Category
from . import roles_required_json

categories_bp = Blueprint("categories_api", __name__, url_prefix="/api/categories")


@categories_bp.route("", methods=["GET"])
def list_categories():
    include_counts = request.args.get("include_counts", "false").lower() == "true"
    active_only = request.args.get("active_only", "false").lower() == "true"

    query = Category.query
    if active_only:
        query = query.filter_by(is_active=True)

    categories = query.order_by(Category.name.asc()).all()
    return (
        jsonify(
            {
                "categories": [c.to_dict(include_counts=include_counts) for c in categories]
            }
        ),
        200,
    )


@categories_bp.route("", methods=["POST"])
@roles_required_json("admin")
def create_category():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()
    is_active = bool(data.get("is_active", True))

    if not name or len(name) < 2 or len(name) > 100:
        return jsonify({"error": "Category name must be between 2 and 100 characters."}), 400

    existing = Category.query.filter(db.func.lower(Category.name) == name.lower()).first()
    if existing:
        return jsonify({"error": f"Category '{name}' already exists."}), 409

    try:
        category = Category(
            name=name,
            description=description[:500] if description else None,
            is_active=is_active,
        )
        db.session.add(category)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Category created successfully.",
                    "category": category.to_dict(include_counts=True),
                }
            ),
            201,
        )
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Category '{name}' already exists."}), 409


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@roles_required_json("admin")
def update_category(category_id: int):
    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"error": "Category not found."}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = str(data["name"]).strip()
        if not name or len(name) < 2 or len(name) > 100:
            return jsonify({"error": "Category name must be between 2 and 100 characters."}), 400
        duplicate = Category.query.filter(
            db.func.lower(Category.name) == name.lower(),
            Category.id != category.id,
        ).first()
        if duplicate:
            return jsonify({"error": f"Category '{name}' already exists."}), 409
        category.name = name

    if "description" in data:
        category.description = str(data["description"]).strip()[:500]

    if "is_active" in data:
        category.is_active = bool(data["is_active"])

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Category updated successfully.",
                    "category": category.to_dict(include_counts=True),
                }
            ),
            200,
        )
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A category with that name already exists."}), 409


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@roles_required_json("admin")
def delete_category(category_id: int):
    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"error": "Category not found."}), 404

    event_count = category.events.count()
    if event_count > 0:
        return (
            jsonify(
                {
                    "error": f"Cannot delete category '{category.name}' because {event_count} event(s) are assigned to it. Reassign those events or deactivate the category instead."
                }
            ),
            409,
        )

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully."}), 200
