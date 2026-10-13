import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app import create_app
from backend.app.models import db
from backend.config import TestingConfig


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    class IsolatedTestConfig(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    test_app = create_app(config_class=IsolatedTestConfig, seed_demo=False)

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, email, password, full_name, role="attendee"):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
            "organization": "Test Org",
        },
    )
    return resp


@pytest.fixture()
def auth_tokens(app, client):
    """
    Creates an admin, two organizers, and two attendees in the isolated test DB
    and returns their Authentication-Token headers and user dicts.
    """
    from flask_security.utils import hash_password
    from backend.app.models import User, Role

    with app.app_context():
        datastore = app.extensions["security"].datastore
        admin_role = Role.query.filter_by(name="admin").first()
        admin_user = datastore.create_user(
            email="admin@test.io",
            password=hash_password("Password123!"),
            full_name="Test Admin",
            active=True,
        )
        datastore.add_role_to_user(admin_user, admin_role)
        db.session.commit()

    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@test.io", "password": "Password123!"},
    ).get_json()

    org1_reg = register_and_login(
        client, "org1@test.io", "Password123!", "Organizer One", role="organizer"
    ).get_json()
    org2_reg = register_and_login(
        client, "org2@test.io", "Password123!", "Organizer Two", role="organizer"
    ).get_json()
    att1_reg = register_and_login(
        client, "att1@test.io", "Password123!", "Attendee One", role="attendee"
    ).get_json()
    att2_reg = register_and_login(
        client, "att2@test.io", "Password123!", "Attendee Two", role="attendee"
    ).get_json()

    return {
        "admin": {
            "token": admin_login["token"],
            "headers": {"Authentication-Token": admin_login["token"]},
            "user": admin_login["user"],
        },
        "org1": {
            "token": org1_reg["token"],
            "headers": {"Authentication-Token": org1_reg["token"]},
            "user": org1_reg["user"],
        },
        "org2": {
            "token": org2_reg["token"],
            "headers": {"Authentication-Token": org2_reg["token"]},
            "user": org2_reg["user"],
        },
        "att1": {
            "token": att1_reg["token"],
            "headers": {"Authentication-Token": att1_reg["token"]},
            "user": att1_reg["user"],
        },
        "att2": {
            "token": att2_reg["token"],
            "headers": {"Authentication-Token": att2_reg["token"]},
            "user": att2_reg["user"],
        },
    }
