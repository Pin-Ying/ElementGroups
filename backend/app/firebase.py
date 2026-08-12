import base64

import pyrebase
import firebase_admin
from firebase_admin import credentials, storage, db

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


def get_image_bytes(symbol):
    """Get element image bytes. Uses GCS Storage when FIREBASE_STORAGE_ENABLED
    (Blaze paid plan), otherwise (or on any Storage failure) falls back to the
    base64 img_data stored in Realtime DB.
    Returns (bytes, content_type) or (None, None) if not found."""
    if settings.FIREBASE_STORAGE_ENABLED:
        try:
            bucket = storage.bucket()
            blob = bucket.blob(f"static/img/{symbol}.JPG")
            return blob.download_as_bytes(), "image/jpeg"
        except Exception as e:
            print(f"GCS read failed for {symbol}, falling back to DB img_data: {e}")

    data = fdb.child(symbol).get()
    img_data = data.get("img_data") if data else None
    if not img_data:
        if symbol == "_default":
            return None, None
        return get_image_bytes("_default")

    header, _, b64 = img_data.partition(",")
    content_type = header.split(":")[1].split(";")[0] if header.startswith("data:") else "image/jpeg"
    try:
        return base64.b64decode(b64), content_type
    except Exception as e:
        # 資料損壞時退回預設圖，而不是讓整個請求 500 造成前台破圖
        print(f"Corrupt img_data for {symbol}: {e}")
        if symbol == "_default":
            return None, None
        return get_image_bytes("_default")


def upload_file(from_f, to_f):
    bucket = storage.bucket()
    blob = bucket.blob(to_f)
    blob.upload_from_filename(from_f)
    return blob.public_url


def upload_fdb(element, datas):
    """寫入資料。

    刻意不吞例外：原本失敗時只印 log 就返回，呼叫端無從得知，
    API 會照常回報成功，使用者以為存好了其實沒有。
    """
    fdb.child(element).set(datas)


def show_fdb_where(node, child_key, value):
    """只取 `node` 底下 `child_key` 等於 `value` 的子項，而不是整個節點。

    為什麼需要這個：像 `_libraries` 這種節點，子項裡含 base64 圖片，整包讀
    下來是好幾 MB。要找「綁在某一類對象上的圖庫」時，只需要其中一小部分。

    RTDB 的 orderBy 查詢需要在資料庫規則加索引：

        "_libraries": { ".indexOn": ["bind_type"] }

    沒有索引時 REST API 會直接回錯誤，所以這裡接住例外並退回整包讀取——
    功能不會壞，只是沒有變快。加了索引之後自動生效，不必再改程式。
    """
    try:
        return fdb.child(node).order_by_child(child_key).equal_to(value).get()
    except Exception as e:
        print(f"[show_fdb_where] {node}.{child_key} 查詢失敗，退回整包讀取：{e}")
        data = fdb.child(node).get()
        if not isinstance(data, dict):
            return data
        return {k: v for k, v in data.items()
                if isinstance(v, dict) and v.get(child_key) == value}


def show_fdb(element=None):
    """讀取資料。找不到節點時回 None，連線或權限錯誤則往上拋。

    同樣不吞例外：讀取失敗回 None 會被上層誤判成「這個元素沒有資料」，
    接著在寫回時用空字串覆蓋掉既有的圖片與故事。
    """
    if element is None:
        return fdb.get()
    return fdb.child(element).get()
