import pyrebase
import firebase_admin
from firebase_admin import credentials, storage, db, exceptions
from google.cloud.exceptions import NotFound

from app.config import settings

json_data = {
    "type": "service_account",
    "project_id": settings.FIREBASE_PROJECT_ID,
    "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
    "private_key": settings.FIREBASE_PRIVATE_KEY,
    "client_email": settings.FIREBASE_CLIENT_EMAIL,
    "client_id": settings.FIREBASE_CLIENT_ID,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL.replace('@', '%40')}",
    "universe_domain": "googleapis.com",
}

cred = credentials.Certificate(json_data)
firebase_admin.initialize_app(
    cred,
    {
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        "databaseURL": settings.FIREBASE_DATABASE_URL,
    },
)

firebase_config = {
    "apiKey": settings.FIREBASE_API_KEY,
    "authDomain": settings.FIREBASE_AUTH_DOMAIN,
    "databaseURL": settings.FIREBASE_DATABASE_URL,
    "projectId": settings.FIREBASE_PROJECT_ID,
    "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
    "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
    "appId": settings.FIREBASE_APP_ID,
    "measurementId": settings.FIREBASE_MEASUREMENT_ID,
}

firebase = pyrebase.initialize_app(firebase_config)
auth_pyrebase = firebase.auth()

fdb = db.reference()
periodic_table_ref = db.reference('periodic_table')


def periodic_table_exists():
    data = periodic_table_ref.order_by_key().limit_to_first(1).get()
    return bool(data)


def upload_periodic_table(elements):
    data = {e['Symbol']: e for e in elements}
    periodic_table_ref.set(data)


def get_periodic_table():
    data = periodic_table_ref.get()
    if not data:
        return []
    return sorted(data.values(), key=lambda e: int(e['AtomicNumber']))


def get_element_by_symbol(symbol):
    return periodic_table_ref.child(symbol).get()


def get_element_by_atomic_number(an):
    data = periodic_table_ref.get()
    if not data:
        return None
    for element in data.values():
        if element.get('AtomicNumber') == str(an):
            return element
    return None


_DEFAULT_IMAGE_PATH = "static/img/Electron.JPG"


def get_image_bytes(symbol):
    """Download element image from Firebase Storage.
    Returns (bytes, content_type) or (None, None) if not found."""
    bucket = storage.bucket()
    blob = bucket.blob(f"static/img/{symbol}.JPG")
    try:
        return blob.download_as_bytes(), "image/jpeg"
    except NotFound:
        default_blob = bucket.blob(_DEFAULT_IMAGE_PATH)
        try:
            return default_blob.download_as_bytes(), "image/jpeg"
        except NotFound:
            return None, None


def upload_file(from_f, to_f):
    bucket = storage.bucket()
    blob = bucket.blob(to_f)
    blob.upload_from_filename(from_f)
    blob.make_public()
    return blob.public_url


def upload_fdb(element, datas):
    try:
        fdb.child(element).set(datas)
    except exceptions.FirebaseError as e:
        print(f"Failed to upload data to Firebase: {e}")


def show_fdb(element=None):
    try:
        if element is None:
            return fdb.get()
        return fdb.child(element).get()
    except Exception as e:
        print(f"Failed to fetch data from Firebase: {e}")
        return None
