"""元素頁面的點閱統計，供首頁「熱門元素」使用。

計數存在 Realtime DB 的 `_stats/{Symbol}/views`。這是寫入頻率相對高
但精確度要求低的資料，因此不做交易鎖，偶爾少算一次無所謂。
"""

from app.firebase import fdb

STATS_NODE = "_stats"


def record_view(symbol):
    """累加一次點閱，回傳累加後的次數。"""
    ref = fdb.child(STATS_NODE).child(symbol).child("views")
    current = ref.get() or 0
    views = int(current) + 1
    ref.set(views)
    return views


def get_all_views():
    """回傳 {Symbol: views}。"""
    data = fdb.child(STATS_NODE).get() or {}
    result = {}
    for symbol, value in data.items():
        if isinstance(value, dict):
            views = value.get("views") or 0
        else:
            views = value or 0
        try:
            result[symbol] = int(views)
        except (TypeError, ValueError):
            continue
    return result
