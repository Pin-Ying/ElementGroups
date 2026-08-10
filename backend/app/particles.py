"""基本粒子形象。

電子、質子、中子這類基本粒子各自有一套設計形象（例如電子是黑白相間、
變化無常又長翅膀的小圓球），需要頁面去呈現（issue #17）。

存在 Realtime DB 的 `_particles/{slug}`。slug 自由新增，不綁死清單，
未來要加光子、夸克都不用改後端。
"""

import re

PARTICLES_NODE = "_particles"

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(raw):
    slug = (raw or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug or not SLUG_PATTERN.match(slug):
        return None
    return slug[:40]


def normalize_particle(slug, data):
    if not isinstance(data, dict):
        return None

    return {
        "slug": slug,
        "name": (data.get("name") or "").strip() or slug,
        # 形象稱呼（例如「長翅膀的小圓球」），與正式名稱分開
        "title": (data.get("title") or "").strip(),
        "description": data.get("description") or "",
        "img_data": (data.get("img_data") or "").strip(),
        # 排序：電子、質子、中子這種固定順序由後台指定
        "order": data.get("order") if isinstance(data.get("order"), int) else 0,
        "published": bool(data.get("published", True)),
        "updated_at": data.get("updated_at") or "",
    }


def normalize_particles(data, include_drafts=False):
    if not isinstance(data, dict):
        return []

    items = []
    for slug, raw in data.items():
        particle = normalize_particle(slug, raw)
        if not particle:
            continue
        if not include_drafts and not particle["published"]:
            continue
        items.append(particle)

    items.sort(key=lambda p: (p["order"], p["slug"]))
    return items


def serialize_particle(payload):
    """整理要寫進 DB 的粒子資料。回傳 (slug, record) 或 (None, 錯誤訊息)。"""
    name = (payload.get("name") or "").strip()
    slug = normalize_slug(payload.get("slug") or name)
    if not slug:
        return None, "無法產生網址代稱，請用英文名稱或自行填寫"
    if not name:
        return None, "請填寫粒子名稱"

    order = payload.get("order")
    return slug, {
        "name": name,
        "title": (payload.get("title") or "").strip(),
        "description": payload.get("description") or "",
        "img_data": (payload.get("img_data") or "").strip(),
        "order": order if isinstance(order, int) else 0,
        "published": bool(payload.get("published", True)),
    }
