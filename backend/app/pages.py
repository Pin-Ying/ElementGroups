"""後台可編輯的頁面。

資料存在 Realtime DB 的 `_pages/{slug}`，內容為 Markdown（渲染在前端做）。
每個頁面可指定要出現在哪個導覽區（頁首／側邊／頁尾／不顯示）與排序，
未發布的頁面只有登入後才讀得到。
"""

import re

PAGES_NODE = "_pages"

NAV_POSITIONS = ("header", "sidebar", "footer", "none")
DEFAULT_NAV = "sidebar"

# 保留給既有路由，避免使用者建出蓋掉功能頁的 slug。
# guide 與 links 刻意不列入：那兩頁的內容本來就開放後台覆寫，
# 前端會以資料庫版本優先，沒有才回退到內建內容。
RESERVED_SLUGS = {"admin", "stroy", "api", "p"}

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(raw):
    """轉成網址友善的 slug；不合法時回傳 None。"""
    slug = (raw or "").strip().lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug or not SLUG_PATTERN.match(slug) or slug in RESERVED_SLUGS:
        return None
    return slug


# 一頁最多幾個區塊。純粹是防呆上限，避免單一頁面大到讀取變慢。
MAX_BLOCKS = 60


def normalize_blocks(raw):
    """頁面區塊。

    刻意只做通用驗證：每個區塊是 {type, data}，type 是非空字串、data 是物件。
    後端不認得任何具體的區塊類型——類型定義住在前端 utils/blockTypes.js，
    因為每一種區塊的「欄位長什麼樣」與「畫出來長什麼樣」本來就是同一份知識，
    拆成前後端兩份只會變成又一個要同步的地方。

    後端不懂類型的代價是：送進來的 data 不會被逐欄位驗證。可接受，因為這是
    只有站長能寫入的後台資料，而讀取端對缺欄位都有預設值。
    """
    if not isinstance(raw, list):
        return []

    blocks = []
    for item in raw[:MAX_BLOCKS]:
        if not isinstance(item, dict):
            continue
        block_type = (item.get("type") or "").strip()
        if not block_type:
            continue
        data = item.get("data")
        blocks.append({"type": block_type, "data": data if isinstance(data, dict) else {}})

    return blocks


def referenced_library_ids(blocks):
    """區塊裡用到的圖庫 id。

    解析區塊圖片時只需要這幾個圖庫，不必把整個 _libraries 讀下來——那裡面
    是所有圖庫的所有 base64。
    """
    found = set()

    def collect(value):
        if isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, dict):
            ref = value.get("image_ref")
            if isinstance(ref, dict) and ref.get("library"):
                found.add(ref["library"])
            for item in value.values():
                collect(item)

    collect(blocks)
    return found


def resolve_block_images(blocks, libraries):
    """把區塊裡的圖庫參照換成實際的圖片 base64。

    區塊存的是 image_ref = {library, image}，前台拿到的則是已經解析好的
    image 字串——這樣渲染端不必知道圖庫的存在，也不必為了畫一張圖再打一次
    API。自己上傳的圖沒有 ref，維持原本的 image 欄位。

    後台不走這裡：編輯時要保留原始的 ref 才能顯示「目前選的是哪一張」，
    預覽則由前端用已經載入的圖庫清單自行解析。
    """
    from app.libraries import image_by_ref

    def resolved(value):
        if not isinstance(value, dict):
            return value
        ref = value.get("image_ref")
        if isinstance(ref, dict) and ref.get("library") and ref.get("image"):
            found = image_by_ref(libraries, ref["library"], ref["image"])
            if found:
                return {**value, "image": found}
        return value

    out = []
    for block in blocks:
        data = dict(block.get("data") or {})
        data = resolved(data)
        # 圖片集的每個子項目也可能是參照
        if isinstance(data.get("images"), list):
            data["images"] = [resolved(item) if isinstance(item, dict) else item
                              for item in data["images"]]
        out.append({**block, "data": data})
    return out


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
        "blocks": normalize_blocks(data.get("blocks")),
        "title": (data.get("title") or "").strip() or slug,
        "subtitle": (data.get("subtitle") or "").strip(),
        # 留空時前台會拿內文開頭當描述
        "seo_description": (data.get("seo_description") or "").strip(),
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
        "blocks": normalize_blocks(payload.get("blocks")),
        "title": title,
        "subtitle": (payload.get("subtitle") or "").strip(),
        "seo_description": (payload.get("seo_description") or "").strip(),
        "content": payload.get("content") or "",
        "nav_position": nav,
        "nav_order": order,
        "published": bool(payload.get("published", False)),
    }
