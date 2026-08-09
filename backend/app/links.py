"""創作者社群連結的資料正規化。

`_creator_links` node 早期只存固定的 {instagram, threads} 兩個欄位，
後來改成不限數量的 links 陣列。這裡統一把兩種格式讀成同一種結構，
讓既有資料不用手動搬遷。
"""

# 舊格式僅有這兩個平台
LEGACY_PLATFORMS = ("instagram", "threads")

LEGACY_LABELS = {
    "instagram": "Instagram",
    "threads": "Threads",
}


def normalize_creator_links(data):
    """把 `_creator_links` 的原始內容轉成 [{platform, label, url}] 陣列。

    無資料時回傳空陣列。
    """
    if not data:
        return []

    links = data.get("links")
    if isinstance(links, list):
        result = []
        for item in links:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            if not url:
                continue
            platform = (item.get("platform") or "website").strip()
            label = (item.get("label") or "").strip() or platform.title()
            result.append({"platform": platform, "label": label, "url": url})
        return result

    # 舊格式：{instagram: "...", threads: "..."}
    result = []
    for platform in LEGACY_PLATFORMS:
        url = (data.get(platform) or "").strip()
        if url:
            result.append({
                "platform": platform,
                "label": LEGACY_LABELS[platform],
                "url": url,
            })
    return result


def serialize_creator_links(payload):
    """把前端送來的 payload 整理成要寫進 DB 的結構。"""
    links = payload.get("links")
    if not isinstance(links, list):
        links = []

    cleaned = []
    for item in links:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        if not url:
            continue
        platform = (item.get("platform") or "website").strip() or "website"
        label = (item.get("label") or "").strip() or platform.title()
        cleaned.append({"platform": platform, "label": label, "url": url})

    return {"links": cleaned}
