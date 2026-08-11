"""元素圖片的分層資料。

原本每個元素只有一張靜態圖，現在拆成三層：

- `nucleus`   原子核，靜態疊圖
- `name_img`  手寫元素名，靜態疊圖
- 電子        不存在元素本身，而是引用共用的「電子樣式」

電子樣式獨立成 `_electron_styles` 節點，是因為同一顆電子的畫法可以套用到
任何元素，沒有必要在每個元素底下各存一份 base64。元素只記錄選了哪一個
樣式（`electron_style`）。

電子怎麼動（`motion`）是全站統一設定，存在 `_motion`。早期版本曾逐個元素
指定，但三種模式是整體視覺風格而非單一元素的特性，逐個設定只是負擔；
舊資料殘留在 `_layers/{symbol}/motion` 的值一律忽略。

三層沒有備齊時，前端會退回原本的靜態圖。
"""

LAYERS_NODE = "_layers"
ELECTRON_STYLES_NODE = "_electron_styles"
# 預設電子樣式的 id 存在這裡；元素沒有各自指定時就用它
ELECTRON_DEFAULT_NODE = "_electron_default"
# 全站電子運動方式
MOTION_NODE = "_motion"

MOTIONS = ("orbit", "free", "static")
DEFAULT_MOTION = "orbit"


def normalize_motion(value):
    """全站電子運動方式；不認得的值一律退回預設。"""
    motion = value.strip() if isinstance(value, str) else ""
    return motion if motion in MOTIONS else DEFAULT_MOTION


def normalize_layers(data):
    """整理單一元素的圖層設定。"""
    if not isinstance(data, dict):
        data = {}

    return {
        "nucleus": (data.get("nucleus") or "").strip(),
        "name_img": (data.get("name_img") or "").strip(),
        "electron_style": (data.get("electron_style") or "").strip(),
    }


def serialize_layers(payload):
    """整理要寫進 DB 的圖層設定。只帶到的欄位才會更新。"""
    record = {}

    for field in ("nucleus", "name_img", "electron_style"):
        if field in payload:
            record[field] = (payload.get(field) or "").strip()

    return record


def resolve_electron_style(layers, default_id):
    """元素沒有指定電子樣式時，退回全站預設。"""
    return (layers.get("electron_style") or "").strip() or (default_id or "").strip()


def normalize_electron_styles(data):
    """共用的電子樣式庫，回傳 [{id, name, img_data}]。"""
    if not isinstance(data, dict):
        return []

    styles = []
    for style_id, raw in data.items():
        if not isinstance(raw, dict):
            continue
        img = (raw.get("img_data") or "").strip()
        if not img:
            continue
        styles.append({
            "id": style_id,
            "name": (raw.get("name") or "").strip() or style_id,
            "img_data": img,
        })

    styles.sort(key=lambda s: s["name"])
    return styles
