import datetime

from flask import Flask, session
from flask_cors import CORS

from app.config import settings
from app.models import alchemy_db
from app.auth import login_manager


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app, supports_credentials=True)

    alchemy_db.init_app(app)
    login_manager.init_app(app)

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = datetime.timedelta(minutes=5)

    from app.routes.public import public_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app
