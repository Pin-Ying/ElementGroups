"""後台可編輯的頁面。

資料存在 Realtime DB 的 `_pages/{slug}`，內容為 Markdown（渲染在前端做）。
每個頁面可指定要出現在哪個導覽區（頁首／側邊／頁尾／不顯示）與排序，
未發布的頁面只有登入後才讀得到。
"""

import re

PAGES_NODE = "_pages"

NAV_POSITIONS = ("header", "sidebar", "footer", "none")
DEFAULT_NAV = "sidebar"

# 保留給既有路由，避免使用者建出蓋掉功能頁的 slug
RESERVED_SLUGS = {"admin", "links", "guide", "stroy", "api", "p"}

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(raw):
    """轉成網址友善的 slug；不合法時回傳 None。"""
    slug = (raw or "").strip().lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug or not SLUG_PATTERN.match(slug) or slug in RESERVED_SLUGS:
        return None
    return slug


def normalize_page(slug, data):
    """把單一頁面的原始資料整理成固定結構。"""
    if not isinstance(data, dict):
        return None

    nav = (data.get("nav_position") or DEFAULT_NAV).strip()
    if nav not in NAV_POSITIONS:
        nav = DEFAULT_NAV

    try:
        order = int(data.get("nav_order") or 0)
    except (TypeError, ValueError):
        order = 0

    return {
        "slug": slug,
        "title": (data.get("title") or "").strip() or slug,
        "content": data.get("content") or "",
        "nav_position": nav,
        "nav_order": order,
        # 未發布 = 草稿，只有登入後看得到
        "published": bool(data.get("published", False)),
        "updated_at": data.get("updated_at") or "",
    }


def normalize_pages(data, include_drafts=False):
    """回傳頁面清單，依 nav_order、title 排序。"""
    if not isinstance(data, dict):
        return []

    pages = []
    for slug, raw in data.items():
        page = normalize_page(slug, raw)
        if not page:
            continue
        if not include_drafts and not page["published"]:
            continue
        pages.append(page)

    pages.sort(key=lambda p: (p["nav_order"], p["title"]))
    return pages


def serialize_page(payload):
    """整理要寫進 DB 的頁面資料。回傳 (slug, record) 或 (None, 錯誤訊息)。"""
    slug = normalize_slug(payload.get("slug"))
    if not slug:
        return None, "網址代稱只能使用小寫英數字與連字號，且不可與既有頁面路徑重複"

    nav = (payload.get("nav_position") or DEFAULT_NAV).strip()
    if nav not in NAV_POSITIONS:
        nav = DEFAULT_NAV

    try:
        order = int(payload.get("nav_order") or 0)
    except (TypeError, ValueError):
        order = 0

    title = (payload.get("title") or "").strip()
    if not title:
        return None, "請填寫頁面標題"

    return slug, {
        "title": title,
        "content": payload.get("content") or "",
        "nav_position": nav,
        "nav_order": order,
        "published": bool(payload.get("published", False)),
    }
