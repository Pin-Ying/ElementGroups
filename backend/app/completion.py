"""元素故事/圖片完成度摘要。

首頁要一眼看出哪些元素已經有圖片或故事，但直接掃整個 DB 會把 118 筆
base64 圖片一起撈下來（`show_fdb()` 沒有欄位投影），對每次首頁載入
來說太重。因此另外維護一個很小的 `_completion` node：

    _completion/{Symbol} = {"story": bool, "image": bool}

寫入故事/圖片時同步更新，讀取時直接取這個 node。若 node 還不存在
（既有資料尚未建立），會自動掃描一次並補寫，之後就走快路徑。
"""

from app.firebase import fdb, show_fdb

COMPLETION_NODE = "_completion"


def _is_element_node(symbol, data):
    return (
        symbol != "periodic_table"
        and not symbol.startswith("_")
        and isinstance(data, dict)
    )


def entry_for(data):
    """從單一元素的資料算出完成度項目。

    updated_at 是首頁「最近更新」用的時間戳；舊資料沒有這個欄位，
    會以空字串表示，排序時會被排除。
    """
    if not isinstance(data, dict):
        return {"story": False, "image": False, "updated_at": ""}
    return {
        "story": bool((data.get("description") or "").strip()),
        "image": bool(data.get("img") or data.get("img_data")),
        "updated_at": data.get("updated_at") or "",
    }


def build_completion_map(fbDatas):
    if not fbDatas:
        return {}
    return {
        symbol: entry_for(data)
        for symbol, data in fbDatas.items()
        if _is_element_node(symbol, data)
    }


def rebuild_completion():
    """掃描整個 DB 重建摘要，回傳新的 map。"""
    completion = build_completion_map(show_fdb())
    fdb.child(COMPLETION_NODE).set(completion)
    return completion


def get_completion():
    """讀取摘要；不存在時掃描一次並補寫。"""
    data = fdb.child(COMPLETION_NODE).get()
    if data:
        return data
    return rebuild_completion()


def update_completion(symbol, data):
    """單一元素寫入後同步更新摘要，失敗不影響主要流程。"""
    try:
        fdb.child(COMPLETION_NODE).child(symbol).set(entry_for(data))
    except Exception as e:
        print(f"Failed to update completion for {symbol}: {e}")
