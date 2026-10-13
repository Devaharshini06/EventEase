import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "eventease-dev-secret-key-change-in-production-9f8a7b6c")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "eventease-dev-password-salt-1a2b3c4d")
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authentication-Token"
    SECURITY_TOKEN_MAX_AGE = int(os.environ.get("SECURITY_TOKEN_MAX_AGE", 86400))  # 24 hours
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_USERNAME_ENABLE = False
    SECURITY_CSRF_PROTECT_MECHANISMS = []
    SECURITY_WTF_CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'eventease.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"timeout": 15, "check_same_thread": False}
    }

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173",
    ).split(",")

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_ENABLED = os.environ.get("CELERY_ENABLED", "false").lower() == "true"


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-isolated"
    SECURITY_PASSWORD_SALT = "test-password-salt-isolated"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECURITY_HASHING_SCHEMES = ["bcrypt"]
    BCRYPT_LOG_ROUNDS = 4


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
