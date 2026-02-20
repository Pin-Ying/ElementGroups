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
users = {}


class User(UserMixin):
    def __init__(self, uid, email):
        self.id = uid
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)


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
        if "EMAIL_NOT_FOUND" in error_message:
            return "Error: Email not found"
        elif "INVALID_PASSWORD" in error_message:
            return "Error: Incorrect password"
        else:
            return f"Error: {error_message}"


@login_required
def logout():
    logout_user()
    return "Logged out successfully"
