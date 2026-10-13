from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


from .user import User, Role, roles_users
from .category import Category
from .event import Event
from .registration import Registration
from .notification import Notification

__all__ = [
    "db",
    "User",
    "Role",
    "roles_users",
    "Category",
    "Event",
    "Registration",
    "Notification",
]
