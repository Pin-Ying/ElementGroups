from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    current_user,
    login_required,
    logout_user,
)
from app.firebase import auth_pyrebase
from firebase_admin import auth

login_manager = LoginManager()
login_manager.session_protection = None  # 停用 IP/UA 識別符檢查，避免 IPv4/IPv6 切換導致 session 失效
users = {}


class User(UserMixin):
    def __init__(self, uid, email):
        self.id = uid
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return users[user_id]
    # Server was restarted (users dict cleared); reconstruct from Firebase
    try:
        firebase_user = auth.get_user(user_id)
        user_obj = User(firebase_user.uid, firebase_user.email)
        users[firebase_user.uid] = user_obj
        return user_obj
    except Exception:
        return None


def login(email, password):
    if not email or not password:
        return "Missing email or password"

    try:
        user = auth_pyrebase.sign_in_with_email_and_password(email, password)
        uid = user["localId"]
        email = user["email"]

        decoded_token = auth.verify_id_token(user["idToken"])
        uid_admin = decoded_token["uid"]

        if uid != uid_admin:
            return "UID mismatch"

        if uid not in users:
            user_obj = User(uid, email)
            users[uid] = user_obj
        else:
            user_obj = users[uid]
        login_user(user_obj)
        return "Login successful"

    except Exception as e:
        error_message = str(e)
        if any(k in error_message for k in ("EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS")):
            return "Incorrect email or password"
        elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_message:
            return "Too many failed attempts, please try again later"
        elif "USER_DISABLED" in error_message:
            return "This account has been disabled"
        else:
            return "Login failed, please try again"


def logout():
    logout_user()
    return "Logged out successfully"
