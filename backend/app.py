"""Examination Management Portal (EMP) – Flask entry point.

Run API        :  python app.py
Celery worker  :  celery -A app.celery worker --loglevel=info
Celery beat    :  celery -A app.celery beat --loglevel=info
"""
import os

from celery import Celery, Task
from flask import Flask, jsonify, g, request
from flask_cors import CORS
from flask_security import Security, SQLAlchemyUserDatastore

from config import Config
from models import db, User, Role
from utils.cache import cache
from utils.helpers import ApiError

datastore = SQLAlchemyUserDatastore(db, User, Role)


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(config_class)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["EXPORT_DIR"], exist_ok=True)
    os.makedirs(app.config["REPORT_DIR"], exist_ok=True)

    db.init_app(app)
    cache.init_app(app)
    CORS(app, supports_credentials=True, expose_headers=["X-Cache", "Content-Disposition"],
         origins=["http://localhost:8080", "http://127.0.0.1:8080"])

    app.security = Security(app, datastore, register_blueprint=False)

    @app.security.unauthn_handler
    def _unauthn(mechanisms=None, headers=None):
        return jsonify({"message": "Please log in to continue (session missing or expired)"}), 401

    @app.security.unauthz_handler
    def _unauthz(func_name=None, params=None):
        return jsonify({"message": "You are not allowed to access this resource"}), 403

    @app.errorhandler(ApiError)
    def _api_error(err):
        db.session.rollback()
        return jsonify({"message": err.message, "errors": err.errors}), err.status

    @app.errorhandler(404)
    def _not_found(_):
        return jsonify({"message": "Resource not found"}), 404

    @app.errorhandler(405)
    def _not_allowed(_):
        return jsonify({"message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def _server_error(_):
        db.session.rollback()
        return jsonify({"message": "Something went wrong on the server"}), 500

    @app.after_request
    def _cache_header(resp):
        status = getattr(g, "cache_status", None)
        if status:
            resp.headers["X-Cache"] = status
        return resp

    # ---- Blueprints (API routes) ----
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.common import common_bp
    from routes.admin import admin_bp
    from routes.examiner import examiner_bp
    from routes.student import student_bp
    for bp in (auth_bp, public_bp, common_bp, admin_bp, examiner_bp, student_bp):
        app.register_blueprint(bp)

    @app.get("/")
    def index():
        return jsonify({"app": "Examination Management Portal API", "status": "running",
                        "frontend": app.config["FRONTEND_URL"]})

    # ---- Create DB programmatically + admin + demo data ----
    with app.app_context():
        from utils.seed import init_database
        init_database(app)

    return app


def celery_init_app(app):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.import_name, task_cls=FlaskTask)
    celery_app.config_from_object("celery_config")
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


app = create_app()
celery = celery_init_app(app)

# register Celery tasks
import tasks.jobs  # noqa: E402,F401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=app.config["DEBUG"])
