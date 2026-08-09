import datetime

from flask import Flask, make_response, request, session

from app.config import settings
from app.auth import login_manager

# 允許的跨來源方法。DELETE 用於刪除電子樣式與頁面，漏掉的話瀏覽器會在
# preflight 階段就擋下請求，前端只會看到操作沒有反應。
CORS_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"


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
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Allow-Methods'] = CORS_METHODS
                # preflight 結果快取一天，減少重複往返
                response.headers['Access-Control-Max-Age'] = '86400'
            return response, 204

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Methods'] = CORS_METHODS
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
