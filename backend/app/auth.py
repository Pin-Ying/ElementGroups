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


def _issue_token(uid, email):
    """發一張後台用的 session token。帳密登入與 Google 登入共用同一種憑證，
    後續的 request_loader 因此不必分辨使用者當初是怎麼進來的。"""
    if uid not in users:
        users[uid] = User(uid, email)

    token = secrets.token_urlsafe(32)
    tokens[token] = uid
    return token


def login_with_google(id_token):
    """用 Firebase 的 Google 供應商登入。

    前端跑完 signInWithPopup 之後會拿到一張 ID token，這裡只負責驗證它是
    真的、而且屬於這個 Firebase 專案，接著一樣走 is_allowed() 的白名單。

    要清楚一件事：**通過 Google 驗證不代表可以進後台。** Google 只證明
    「這個人是這個 email 的擁有者」，任何人用自己的 Google 帳號都能走完
    這段流程。真正擋下來的是 ADMIN_ACCOUNTS，沒設定的話這條路等於大門
    敞開——比帳密登入更糟，因為連註冊那一步都省了。
    """
    if not settings.GOOGLE_LOGIN_ENABLED:
        return None, "Google 登入未啟用"
    if not id_token:
        return None, "Missing token"

    try:
        decoded = auth.verify_id_token(id_token)
    except Exception as e:
        # 這裡刻意不把原始錯誤丟回前端：verify_id_token 的訊息會夾帶專案
        # ID 與憑證細節。log 留完整內容給站長查。
        print(f"[auth] Google ID token 驗證失敗：{e}")
        message = str(e)
        if "expired" in message.lower():
            return None, "登入逾時，請再登入一次"
        return None, "登入失敗，請再試一次"

    uid = decoded.get("uid") or decoded.get("sub") or ""
    email = decoded.get("email", "")

    # 和帳密登入不同，這裡給的是明確訊息。帳密登入之所以含糊其辭，是為了
    # 不讓人試出「這個 email 有註冊」；但走到這一步的人已經證明自己擁有
    # 這個 Google 帳號，講清楚不會洩漏任何東西，反而是站長自己 ADMIN_ACCOUNTS
    # 填錯時唯一能看出問題的線索。
    if not is_allowed(uid, email):
        print(f"[auth] 拒絕非管理員的 Google 登入：{email or uid}")
        return None, "這個 Google 帳號沒有後台權限"

    return _issue_token(uid, email), "Login successful"


def login(email, password):
    # 擋在後端而不是只把前端表單藏起來——這支端點是公開的，繞過畫面直接
    # 打就行，前端隱藏只是視覺效果，沒有任何安全意義
    if not settings.password_login_enabled:
        return None, "此站已改用 Google 帳號登入"

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

        return _issue_token(uid, email), "Login successful"

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
