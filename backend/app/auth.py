import secrets

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    current_user,
    logout_user,
)
from app.config import settings
from app.firebase import auth_pyrebase
from firebase_admin import auth

login_manager = LoginManager()
login_manager.session_protection = None
users = {}   # uid -> User
tokens = {}  # token -> uid


class User(UserMixin):
    def __init__(self, uid, email):
        self.id = uid
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return users[user_id]
    try:
        firebase_user = auth.get_user(user_id)
        user_obj = User(firebase_user.uid, firebase_user.email)
        users[firebase_user.uid] = user_obj
        return user_obj
    except Exception:
        return None


@login_manager.request_loader
def load_user_from_request(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    uid = tokens.get(token)
    if not uid:
        return None
    if uid in users:
        return users[uid]
    try:
        firebase_user = auth.get_user(uid)
        user_obj = User(firebase_user.uid, firebase_user.email)
        users[uid] = user_obj
        return user_obj
    except Exception:
        return None


def _allowed_accounts():
    """設定裡允許登入的帳號，正規化成小寫集合。空集合代表沒有設定。"""
    return {a.strip().lower() for a in settings.ADMIN_ACCOUNTS.split(",") if a.strip()}


def is_allowed(uid, email):
    """這個帳號可以進後台嗎？

    沒設定 ADMIN_ACCOUNTS 就一律放行——這是為了不讓既有部署在更新後突然
    登不進去，但那等於沒有這道鎖，所以會每次都叫。
    """
    allowed = _allowed_accounts()
    if not allowed:
        print(
            "[auth] 警告：未設定 ADMIN_ACCOUNTS，任何在這個 Firebase 專案裡"
            "有效的帳號都能登入後台。請填入自己的 UID 或 email。"
        )
        return True
    return uid.lower() in allowed or (email or "").lower() in allowed


def login(email, password):
    if not email or not password:
        return None, "Missing email or password"

    try:
        user = auth_pyrebase.sign_in_with_email_and_password(email, password)
        uid = user["localId"]
        email = user["email"]

        decoded_token = auth.verify_id_token(user["idToken"])
        uid_admin = decoded_token["uid"]

        if uid != uid_admin:
            return None, "UID mismatch"

        # 帳密是對的，但不是站長。錯誤訊息刻意和密碼錯誤一模一樣——講出
        # 「這個帳號不能進後台」等於告訴對方帳號存在、只是權限不夠
        if not is_allowed(uid, email):
            print(f"[auth] 拒絕非管理員登入：{email}")
            return None, "Incorrect email or password"

        if uid not in users:
            users[uid] = User(uid, email)

        token = secrets.token_urlsafe(32)
        tokens[token] = uid
        return token, "Login successful"

    except Exception as e:
        error_message = str(e)
        if any(k in error_message for k in ("EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS")):
            return None, "Incorrect email or password"
        elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_message:
            return None, "Too many failed attempts, please try again later"
        elif "USER_DISABLED" in error_message:
            return None, "This account has been disabled"
        else:
            return None, "Login failed, please try again"


def logout(token=None):
    if token and token in tokens:
        del tokens[token]
    logout_user()
    return "Logged out successfully"
