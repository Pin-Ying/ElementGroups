"""通用圖庫。

專案裡帶圖的東西原本各自為政：元素代表圖是 `{Symbol}/img_data`、其他樣貌
是 `_gallery/{Symbol}[]`、電子樣式是 `_electron_styles/{id}`、粒子與主族與
分子各有自己的 `img_data`。每加一個帶圖的東西就得重寫一套 CRUD，而且結構
還不一樣（有的是陣列＋caption，有的是 map＋name）。

這個模組把「一組圖」抽成獨立的實體：

    _libraries/{library_id} = {
      name, bind_type, bind_id, default_image, images: {...}
    }

`bind_type` 是接點——它說明這個圖庫能用在哪一「類」東西上，`bind_id` 指到
具體哪一個。要讓新的東西也能有圖庫，只需要在下面的 BINDABLE_TYPES 加一筆，
不必再寫一套端點與後台介面。

刻意不動既有的節點：這裡是新增的一層，舊功能照常運作，之後想搬哪一個再
一個一個搬。
"""

import datetime
import re

LIBRARIES_NODE = "_libraries"

# 一個圖庫最多幾張圖。base64 直接存在 Realtime DB，太多會讓單次讀取過重，
# 與 _gallery 的上限（6）取同一個量級但放寬一些。
MAX_IMAGES = 12

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ── 接點：哪些東西可以有圖庫 ────────────────────────────────────────
#
# node       對象清單所在的 Realtime DB 節點；None 表示不綁特定對象（全站）
# id_field   從節點資料取出識別碼的欄位；None 表示用 key 當識別碼
# name_field 後台下拉顯示的名稱欄位
#
# 新增一種可綁對象時只改這裡。前端的下拉選單、後端的驗證都是讀這份定義，
# 不會有第二個地方要同步。
BINDABLE_TYPES = {
    "particle": {
        "label": "基本粒子",
        "node": "_particles",
        "id_field": None,
        "name_field": "name",
    },
    "element": {
        "label": "元素",
        "node": "periodic_table",
        "id_field": "Symbol",
        "name_field": "Name",
    },
    "group": {
        "label": "主族",
        "node": "_element_groups",
        "id_field": None,
        "name_field": "name",
    },
    "molecule": {
        "label": "分子",
        "node": "_molecules",
        "id_field": None,
        "name_field": "name",
    },
    "site": {
        "label": "網站整體",
        "node": None,
        "id_field": None,
        "name_field": None,
    },
}


def bindable_definitions():
    """給前端的接點定義。只回傳畫介面需要的欄位。"""
    return [
        {"key": key, "label": cfg["label"], "needs_target": cfg["node"] is not None}
        for key, cfg in BINDABLE_TYPES.items()
    ]


def normalize_slug(raw):
    slug = (raw or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug or not ID_PATTERN.match(slug):
        return None
    return slug[:40]


def normalize_images(data):
    """圖片整理成 [{id, name, img_data, order}]，依 order 排序。

    存進 DB 時是 map（才好單張增刪），對外一律轉成排序過的陣列。
    """
    if not isinstance(data, dict):
        return []

    images = []
    for image_id, raw in data.items():
        if not isinstance(raw, dict):
            continue
        img = (raw.get("img_data") or "").strip()
        if not img:
            continue
        try:
            order = int(raw.get("order") or 0)
        except (TypeError, ValueError):
            order = 0
        images.append({
            "id": image_id,
            "name": (raw.get("name") or "").strip() or image_id,
            "img_data": img,
            "order": order,
        })

    images.sort(key=lambda i: (i["order"], i["name"]))
    return images


def normalize_library(library_id, data):
    """單一圖庫。bind_type 不認得時視為無效，回 None。"""
    if not isinstance(data, dict):
        return None

    bind_type = (data.get("bind_type") or "").strip()
    if bind_type not in BINDABLE_TYPES:
        return None

    # 不綁特定對象的類型（site）忽略 bind_id，避免存進去的殘值造成誤判
    bind_id = (data.get("bind_id") or "").strip()
    if BINDABLE_TYPES[bind_type]["node"] is None:
        bind_id = ""

    images = normalize_images(data.get("images"))
    default_image = (data.get("default_image") or "").strip()
    # 預設圖被刪掉時不要留下指向不存在的 id
    if default_image and not any(i["id"] == default_image for i in images):
        default_image = ""

    return {
        "id": library_id,
        "name": (data.get("name") or "").strip() or library_id,
        "bind_type": bind_type,
        "bind_id": bind_id,
        "default_image": default_image,
        "images": images,
        "updated_at": data.get("updated_at") or "",
    }


def normalize_libraries(data):
    if not isinstance(data, dict):
        return []

    libraries = []
    for library_id, raw in data.items():
        lib = normalize_library(library_id, raw)
        if lib:
            libraries.append(lib)

    libraries.sort(key=lambda l: (l["bind_type"], l["bind_id"], l["name"]))
    return libraries


def serialize_library(payload):
    """整理要寫進 DB 的圖庫。回傳 (library_id, record) 或 (None, 錯誤訊息)。"""
    name = (payload.get("name") or "").strip()
    if not name:
        return None, "請填寫圖庫名稱"

    bind_type = (payload.get("bind_type") or "").strip()
    if bind_type not in BINDABLE_TYPES:
        return None, "不認得的綁定類型"

    cfg = BINDABLE_TYPES[bind_type]
    bind_id = (payload.get("bind_id") or "").strip()
    if cfg["node"] is not None and not bind_id:
        return None, f"請選擇要綁定的{cfg['label']}"
    if cfg["node"] is None:
        bind_id = ""

    library_id = normalize_slug(payload.get("id")) or _new_id()

    images = {}
    raw_images = payload.get("images")
    if isinstance(raw_images, list):
        if len(raw_images) > MAX_IMAGES:
            return None, f"一個圖庫最多 {MAX_IMAGES} 張圖"
        for order, item in enumerate(raw_images):
            if not isinstance(item, dict):
                continue
            img = (item.get("img_data") or "").strip()
            if not img:
                continue
            image_id = normalize_slug(item.get("id")) or _new_id("img")
            images[image_id] = {
                "name": (item.get("name") or "").strip() or image_id,
                "img_data": img,
                "order": order,
            }

    default_image = (payload.get("default_image") or "").strip()
    if default_image and default_image not in images:
        default_image = ""

    return library_id, {
        "name": name,
        "bind_type": bind_type,
        "bind_id": bind_id,
        "default_image": default_image,
        "images": images,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def _new_id(prefix="lib"):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}-{stamp}"


def library_id_for(bind_type, bind_id):
    """綁定對關係固定對應一個 library id，搬遷與查詢才不會各自生出不同的 id。"""
    suffix = normalize_slug(bind_id) or "default"
    return f"{bind_type}-{suffix}"


def find_library(libraries, bind_type, bind_id=""):
    """取綁在某個對象上的圖庫；沒有就回 None。"""
    return next(iter(libraries_for(libraries, bind_type, bind_id)), None)


def libraries_for(libraries, bind_type, bind_id=""):
    """查某個對象有哪些圖庫。"""
    return [
        l for l in libraries
        if l["bind_type"] == bind_type and (not bind_id or l["bind_id"] == bind_id)
    ]


def primary_image_data(libraries, bind_type, bind_id):
    """某個對象的代表圖：圖庫的預設圖，沒設定就第一張。沒有圖庫時回空字串。

    讓「單張 img_data」的舊欄位可以無痛換成「圖庫的預設圖」——呼叫端拿到
    的一樣是一個 base64 字串，不必知道背後換了資料來源。
    """
    image = resolve_image(find_library(libraries, bind_type, bind_id))
    return image["img_data"] if image else ""


def resolve_image(library, image_id=""):
    """從圖庫挑一張圖：指定的優先，其次預設，最後第一張。"""
    if not library or not library["images"]:
        return None

    if image_id:
        for img in library["images"]:
            if img["id"] == image_id:
                return img

    if library["default_image"]:
        for img in library["images"]:
            if img["id"] == library["default_image"]:
                return img

    return library["images"][0]
