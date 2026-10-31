"""Application configuration.

All values can be overridden with environment variables so the same code runs
on any machine (WSL / Linux / macOS) without edits.
"""
import os
import time

# All dates/times in the app use Indian Standard Time, even if WSL runs in UTC
os.environ["TZ"] = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
if hasattr(time, "tzset"):
    time.tzset()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    SECRET_KEY = os.getenv("SECRET_KEY", "emp-v2-super-secret-key-change-me")

    # ---- Database (SQLite only) ----
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "emp.sqlite3")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Flask-Security-Too (token based auth) ----
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "emp-v2-password-salt")
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authentication-Token"
    SECURITY_TOKEN_MAX_AGE = 60 * 60 * 24  # 24 hours
    SECURITY_TRACKABLE = False
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
    WTF_CSRF_ENABLED = False
    SECURITY_FRESHNESS_GRACE_PERIOD = 0

    # ---- Redis cache ----
    CACHE_TYPE = os.getenv("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "redis://localhost:6379/2")
    CACHE_DEFAULT_TIMEOUT = 120
    CACHE_KEY_PREFIX = "emp:"

    # ---- Mail (MailHog for local demo) ----
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_SENDER = os.getenv("MAIL_SENDER", "EMP Portal <no-reply@emp.local>")

    # ---- Admin (created programmatically) ----
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@emp.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Portal Administrator")

    # ---- Seed demo data on first run ----
    SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "1") == "1"

    # ---- Frontend URL (used inside e-mails) ----
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
    REPORT_DIR = os.path.join(BASE_DIR, "reports")
