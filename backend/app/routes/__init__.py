from functools import wraps
from flask import jsonify
from flask_security import current_user, auth_required


def token_auth_required(fn):
    """
    Wraps Flask-Security-Too's @auth_required('token') and ensures deactivated accounts
    are rejected with 403 even if a token was recently issued.
    """
    @wraps(fn)
    @auth_required("token")
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required."}), 401
        if not current_user.active:
            return jsonify({"error": "Your user account has been deactivated."}), 403
        return fn(*args, **kwargs)

    return decorated


def roles_required_json(*role_names):
    """
    Server-side role-based access enforcement using Flask-Security-Too's current_user roles.
    Returns 401 if unauthenticated, 403 if deactivated or lacking required role.
    """
    def wrapper(fn):
        @wraps(fn)
        @auth_required("token")
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required."}), 401
            if not current_user.active:
                return jsonify({"error": "Your user account has been deactivated."}), 403
            if not any(current_user.has_role(role) for role in role_names):
                return (
                    jsonify(
                        {
                            "error": f"Insufficient permissions. Required role(s): {', '.join(role_names)}."
                        }
                    ),
                    403,
                )
            return fn(*args, **kwargs)

        return decorated

    return wrapper
