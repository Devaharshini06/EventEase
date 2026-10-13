from flask import Flask, jsonify
from flask_cors import CORS
from flask_security import Security, SQLAlchemyUserDatastore
from ..config import Config
from .models import db, User, Role
from .routes.auth import auth_bp
from .routes.categories import categories_bp
from .routes.events import events_bp
from .routes.registrations import registrations_bp
from .routes.dashboards import dashboards_bp
from .routes.users import users_bp
from .services import seed_initial_data


def create_app(config_class=Config, seed_demo: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore, register_blueprint=False)

    @security.unauthn_handler
    def handle_unauthenticated(mechanisms, headers=None):
        return (
            jsonify(
                {
                    "error": "Authentication required or token is invalid/expired.",
                    "mechanisms": mechanisms,
                }
            ),
            401,
        )

    @security.unauthz_handler
    def handle_unauthorized(func_name, params):
        return (
            jsonify(
                {
                    "error": "Insufficient role permissions to access this resource.",
                    "required_roles": params,
                }
            ),
            403,
        )

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get("CORS_ORIGINS", ["*"]),
                "allow_headers": ["Content-Type", "Authentication-Token", "Authorization"],
                "expose_headers": ["Content-Disposition"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            }
        },
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(registrations_bp)
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(users_bp)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "EventEase Flask API"}), 200

    @app.errorhandler(404)
    def handle_404(err):
        return jsonify({"error": "Requested endpoint or resource was not found."}), 404

    @app.errorhandler(405)
    def handle_405(err):
        return jsonify({"error": "HTTP method not allowed for this endpoint."}), 405

    @app.errorhandler(500)
    def handle_500(err):
        db.session.rollback()
        return jsonify({"error": "An unexpected internal server error occurred."}), 500

    with app.app_context():
        db.create_all()
        should_seed_demo = seed_demo and not app.config.get("TESTING", False)
        seed_initial_data(user_datastore, seed_demo_records=should_seed_demo)

    return app
