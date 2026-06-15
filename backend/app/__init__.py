import datetime

from flask import Flask, make_response, request, session

from app.config import settings
from app.auth import login_manager


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(minutes=10)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin', '')
            response = make_response()
            if origin == settings.FRONTEND_URL:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            return response, 204

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '')
        if origin == settings.FRONTEND_URL:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

    login_manager.init_app(app)

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    from app.routes.public import public_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app
