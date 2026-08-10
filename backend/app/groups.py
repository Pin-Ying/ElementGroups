"""主族形象。

每個族（1A–8A、1B–10B、鑭系、錒系）可以各自設定一套形象：
同族元素性質相近，設計上共用特色（例如 7A 是型態不穩定的獵食鳥類、
8A 是圓胖胖又穩定的物種），類似寶可夢依體型分出的系列。

存在 Realtime DB 的 `_element_groups/{key}`。元素屬於哪一族由前端的
週期表位置對照表推得，後端只負責形象內容本身。
"""

# 族的順序也用於後台清單與前台總覽的排列：A 族優先（性質最一致），
# 再來 B 族，最後鑭系錒系
GROUP_KEYS = (
    "1A", "2A", "3A", "4A", "5A", "6A", "7A", "8A",
    "1B", "2B", "3B", "4B", "5B", "6B", "7B", "8B", "9B", "10B",
    "Lanthanides", "Actinides",
)

GROUPS_NODE = "_element_groups"


def normalize_group(key, data):
    """整理單一族的形象設定。"""
    if not isinstance(data, dict):
        data = {}

    return {
        "key": key,
        # 形象名稱（例如「獵食鳥系」），非族名本身
        "name": (data.get("name") or "").strip(),
        # 共同特色與設計說明
        "description": (data.get("description") or "").strip(),
        # 形象代表圖（base64）
        "img_data": (data.get("img_data") or "").strip(),
        "updated_at": data.get("updated_at") or "",
    }


def normalize_groups(data):
    """整理所有族的形象，固定依 GROUP_KEYS 排序。"""
    if not isinstance(data, dict):
        data = {}
    return [normalize_group(key, data.get(key)) for key in GROUP_KEYS]


def serialize_group(payload):
    """整理要寫進 DB 的形象設定。回傳 record 或 None（無效輸入）。"""
    if not isinstance(payload, dict):
        return None

    return {
        "name": (payload.get("name") or "").strip(),
        "description": (payload.get("description") or "").strip(),
        "img_data": (payload.get("img_data") or "").strip(),
    }


def has_content(group):
    """判斷這個族是否已經設定過形象，前台只顯示有內容的族。"""
    return bool(group.get("name") or group.get("description") or group.get("img_data"))
