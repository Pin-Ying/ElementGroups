"""列出這個 Firebase 專案裡所有能登入的帳號。

用途有兩個：

1. 查出自己的 UID，填進 `.env` 的 `ADMIN_ACCOUNTS`
2. 檢查有沒有你不認得的帳號——`login()` 原本只驗證帳密在這個專案裡有效，
   所以任何一個帳號都能進後台

    python scripts/list_auth_users.py

需要 Firebase 憑證（讀的是 Firebase Auth，不是 Realtime Database）。
"""

import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# app/__init__.py 會 import auth，這裡只要 firebase 本身
_pkg = types.ModuleType("app")
_pkg.__path__ = [os.path.join(_ROOT, "app")]
sys.modules.setdefault("app", _pkg)

from firebase_admin import auth  # noqa: E402

import app.firebase  # noqa: E402,F401  初始化 firebase_admin

from app.config import settings  # noqa: E402


def main():
    allowed = {a.strip().lower() for a in settings.ADMIN_ACCOUNTS.split(",") if a.strip()}

    rows = []
    page = auth.list_users()
    while page:
        for user in page.users:
            rows.append(user)
        page = page.get_next_page()

    if not rows:
        print("這個專案沒有任何帳號。")
        return 0

    print(f"{'UID':30} {'Email':34} {'狀態':6} 可進後台")
    print("-" * 88)
    for u in rows:
        uid = u.uid
        email = u.email or "（無）"
        state = "停用" if u.disabled else "啟用"
        ok = "是" if (not allowed or uid.lower() in allowed or (u.email or "").lower() in allowed) else "否"
        print(f"{uid:30} {email:34} {state:6} {ok}")

    print()
    if not allowed:
        print("目前沒有設定 ADMIN_ACCOUNTS，所以上面每一個帳號都能進後台。")
        print("把你自己那一行的 UID（或 email）填進 .env：")
        print(f"    ADMIN_ACCOUNTS={rows[0].email or rows[0].uid}")
    else:
        print(f"目前允許：{', '.join(sorted(allowed))}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
