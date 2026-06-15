import datetime

from flask import Flask, session
from flask_cors import CORS

from app.config import settings
from app.auth import login_manager


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(minutes=10)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True  # 每次 request 重置過期時間
    app.config["SESSION_COOKIE_SAMESITE"] = "None"     # 允許跨域攜帶 cookie
    app.config["SESSION_COOKIE_SECURE"] = True          # SameSite=None 必須搭配 Secure

    CORS(app, supports_credentials=True)

    login_manager.init_app(app)

    @app.before_request
    def make_session_permanent():
        session.permanent = True  # 使用 PERMANENT_SESSION_LIFETIME 而非 browser session

    from app.routes.public import public_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app
