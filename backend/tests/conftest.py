"""測試共用設定。

## 為什麼不直接 `from app.config import settings`

`app` 是 package，import 它底下任何模組都會先執行 `app/__init__.py`，
而那裡 import 了 flask 與 `app.auth`，`app.auth` 又 import `app.firebase`
——後者在 **import 階段**就初始化 Firebase Admin SDK。所以在沒有真實憑證
的環境（本機、CI）光是 import 就會炸掉。

這不是測試的問題，是模組 import 有副作用。真要根治得把 SDK 初始化改成
延遲執行，那會動到不少地方，暫時先繞過：用 importlib 直接載入單一 .py
檔案，不經過 package 的 `__init__`。

代價是只能測「不依賴 app 內其他模組」的檔案。目前 config.py 與
molecules.py 都符合，它們本來就只依賴標準函式庫與 pydantic。
"""

import importlib.util
import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Settings 有一堆必填欄位，沒有值連 class 都定義不出實例。這裡給一組假值，
# 測試要驗的是設定之間的邏輯，不是這些值本身。
FAKE_ENV = {
    "SECRET_KEY": "test-secret",
    "FIREBASE_PROJECT_ID": "test-project",
    "FIREBASE_PRIVATE_KEY_ID": "test-key-id",
    "FIREBASE_PRIVATE_KEY": "test-key",
    "FIREBASE_CLIENT_EMAIL": "test@example.invalid",
    "FIREBASE_CLIENT_ID": "test-client",
    "FIREBASE_STORAGE_BUCKET": "test-bucket",
    "FIREBASE_DATABASE_URL": "https://test.invalid/",
    "FIREBASE_API_KEY": "test-api-key",
    "FIREBASE_AUTH_DOMAIN": "test.invalid",
    "FIREBASE_MESSAGING_SENDER_ID": "0",
    "FIREBASE_APP_ID": "test-app-id",
    "FIREBASE_MEASUREMENT_ID": "test-measurement",
}


def load_app_module(name):
    """直接從檔案載入 backend/app/<name>.py，不觸發 app/__init__.py。"""
    path = os.path.join(BACKEND_ROOT, "app", f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_isolated_{name}", path)
    module = importlib.util.module_from_spec(spec)
    # 有些模組會 import 自己所在的 package，先放進 sys.modules 避免重複載入
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
