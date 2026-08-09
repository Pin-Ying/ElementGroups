"""創作者社群連結的資料正規化。

`_creator_links` 經歷過三種格式，這裡統一讀成同一種結構，讓既有資料
不用手動搬遷：

1. 最早：{instagram: url, threads: url}
2. 其次：{links: [{platform, label, url}]}
3. 現在：{description, avatar_shape, links: [{platform, label, url, color, avatar}]}
"""

# 最早期的格式僅有這兩個平台
LEGACY_PLATFORMS = ("instagram", "threads")

LEGACY_LABELS = {
    "instagram": "Instagram",
    "threads": "Threads",
}

AVATAR_SHAPES = ("circle", "square")
DEFAULT_SHAPE = "circle"


def _clean_link(item):
    """整理單筆連結；沒有網址的視為無效。"""
    if not isinstance(item, dict):
        return None
    url = (item.get("url") or "").strip()
    if not url:
        return None
    platform = (item.get("platform") or "website").strip() or "website"
    return {
        "platform": platform,
        "label": (item.get("label") or "").strip() or platform.title(),
        "url": url,
        # 自訂顏色，留空則沿用前端的平台預設色
        "color": (item.get("color") or "").strip(),
        # 頭像 base64，留空則顯示文字
        "avatar": (item.get("avatar") or "").strip(),
    }


def _legacy_links(data):
    result = []
    for platform in LEGACY_PLATFORMS:
        url = (data.get(platform) or "").strip()
        if url:
            result.append({
                "platform": platform,
                "label": LEGACY_LABELS[platform],
                "url": url,
                "color": "",
                "avatar": "",
            })
    return result


def normalize_creator_links(data):
    """回傳 {description, avatar_shape, links}。無資料時給空的預設值。"""
    if not data:
        return {"description": "", "avatar_shape": DEFAULT_SHAPE, "links": []}

    raw_links = data.get("links")
    if isinstance(raw_links, list):
        links = [c for c in (_clean_link(i) for i in raw_links) if c]
    else:
        links = _legacy_links(data)

    shape = (data.get("avatar_shape") or DEFAULT_SHAPE).strip()
    if shape not in AVATAR_SHAPES:
        shape = DEFAULT_SHAPE

    return {
        "description": (data.get("description") or "").strip(),
        "avatar_shape": shape,
        "links": links,
    }


def serialize_creator_links(payload):
    """把前端送來的 payload 整理成要寫進 DB 的結構。"""
    raw_links = payload.get("links")
    if not isinstance(raw_links, list):
        raw_links = []

    shape = (payload.get("avatar_shape") or DEFAULT_SHAPE).strip()
    if shape not in AVATAR_SHAPES:
        shape = DEFAULT_SHAPE

    return {
        "description": (payload.get("description") or "").strip(),
        "avatar_shape": shape,
        "links": [c for c in (_clean_link(i) for i in raw_links) if c],
    }
