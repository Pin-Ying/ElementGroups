"""把 Realtime Database 的 `.indexOn` 索引寫進資料庫規則。

為什麼需要索引：`show_fdb_where()` 用 RTDB 的 orderBy 查詢只取需要的圖庫，
而不是把整個 `_libraries`（所有圖庫的所有 base64）讀下來。orderBy 在沒有
索引的路徑上會被 REST API 直接拒絕，程式雖然有 fallback 不會壞，但也就沒
有變快。

規則可以用程式改：RTDB 有一支 `/.settings/rules.json` 端點，用專案既有的
service account 換一個 access token 就能存取，不必開主控台。

**這支腳本會覆寫整份規則**，所以做法是先讀下來、備份、只加上缺的索引、
印出差異，確認之後才寫回：

    python scripts/ensure_db_index.py            # 只看要改什麼（預設不寫入）
    python scripts/ensure_db_index.py --apply    # 真的寫回

只會新增 `.indexOn`，不會動到任何 `.read` / `.write` 規則。萬一寫壞了，
備份檔可以直接貼回主控台。

如果規則裡有註解（主控台允許，但那不是合法 JSON），這支腳本會拒絕動作並
請你手動加——寧可不做，也不要把有註解的規則解析壞。
"""

import argparse
import copy
import datetime
import json
import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# 同 try_ai.py：app/__init__.py 會連帶初始化 Firebase，這裡只要設定值
_pkg = types.ModuleType("app")
_pkg.__path__ = [os.path.join(_ROOT, "app")]
sys.modules.setdefault("app", _pkg)

import requests  # noqa: E402
from google.auth.transport.requests import Request  # noqa: E402
from google.oauth2 import service_account  # noqa: E402

from app.config import settings  # noqa: E402

SCOPES = [
    "https://www.googleapis.com/auth/firebase.database",
    "https://www.googleapis.com/auth/userinfo.email",
]

# 要確保存在的索引。key 是節點路徑，value 是要 orderBy 的欄位。
# 與 app/firebase.py 的 show_fdb_where() 呼叫端對應——那裡多一種查詢，
# 這裡就要多一個欄位，否則新的查詢會落回整包讀取。
REQUIRED_INDEXES = {
    "_libraries": ["bind_type", "bind_id"],
}


def _credentials():
    info = {
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY,
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    creds.refresh(Request())
    return creds


def _rules_url():
    return settings.FIREBASE_DATABASE_URL.rstrip("/") + "/.settings/rules.json"


def _merge(rules):
    """把缺少的索引加進規則。回傳 (新規則, 這次新增了什麼)。"""
    merged = copy.deepcopy(rules)
    added = []

    for node, fields in REQUIRED_INDEXES.items():
        target = merged.setdefault("rules", {}).setdefault(node, {})
        if not isinstance(target, dict):
            raise ValueError(f"規則裡的 {node} 不是物件，無法自動加索引")

        current = target.get(".indexOn", [])
        if isinstance(current, str):
            current = [current]

        missing = [f for f in fields if f not in current]
        if missing:
            target[".indexOn"] = current + missing
            added.append(f"{node}: {', '.join(missing)}")

    return merged, added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="真的寫回規則（預設只顯示差異）")
    args = parser.parse_args()

    token = _credentials().token
    url = _rules_url()

    res = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if res.status_code != 200:
        print(f"讀取規則失敗（{res.status_code}）：{res.text[:300]}", file=sys.stderr)
        print("service account 需要 Firebase 資料庫管理權限。", file=sys.stderr)
        return 1

    try:
        rules = json.loads(res.text)
    except json.JSONDecodeError:
        print("目前的規則不是合法 JSON（通常是裡面有註解）。", file=sys.stderr)
        print("自動合併會把註解弄掉，所以這裡不動作，請到主控台手動加：", file=sys.stderr)
        for node, fields in REQUIRED_INDEXES.items():
            print(f'  "{node}": {{ ".indexOn": {json.dumps(fields)} }}', file=sys.stderr)
        return 1

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(_ROOT, f"db-rules-backup-{stamp}.json")
    with open(backup, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    print(f"目前的規則已備份到 {backup}")

    merged, added = _merge(rules)
    if not added:
        print("索引都已經存在，不需要更動。")
        return 0

    print("\n這次會新增：")
    for line in added:
        print(f"  {line}")

    if not args.apply:
        print("\n這是預覽。確認沒問題後加 --apply 才會真的寫回。")
        return 0

    put = requests.put(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(merged),
        timeout=30,
    )
    if put.status_code != 200:
        print(f"\n寫入失敗（{put.status_code}）：{put.text[:300]}", file=sys.stderr)
        print(f"規則沒有被改動，備份仍在 {backup}", file=sys.stderr)
        return 1

    print("\n已寫入。show_fdb_where() 的查詢從現在起會走索引，不再落回整包讀取。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
