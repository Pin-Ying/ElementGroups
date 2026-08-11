"""元素圖片的分層資料。

原本每個元素只有一張靜態圖，現在拆成三層：

- `nucleus`   原子核，靜態疊圖，每個元素各自上傳
- `name_img`  手寫元素名，靜態疊圖，每個元素各自上傳
- 繞行粒子    不存在元素本身，而是引用「基本粒子」（`_particles`）的形象

繞行粒子早期是獨立的 `_electron_styles` 節點，只認電子。但 `_particles`
本來就是可自由新增的粒子形象庫（電子、質子、中子，之後要加光子夸克也
不用改後端），兩邊各養一套圖沒有意義，所以改成直接引用它，並且和運動
方式一樣是全站統一設定。

全站設定：

- `_orbit_particle`  繞行粒子的 slug，指向 `_particles/{slug}`
- `_motion`          怎麼動；三種模式是整體視覺風格而非單一元素的特性

舊資料殘留在 `_layers/{symbol}` 的 `electron_style` 與 `motion` 一律忽略。

三層沒有備齊時，前端會退回原本的靜態圖。
"""

LAYERS_NODE = "_layers"
# 全站繞行粒子的 slug
ORBIT_PARTICLE_NODE = "_orbit_particle"
# 全站電子運動方式
MOTION_NODE = "_motion"

MOTIONS = ("orbit", "free", "static")
DEFAULT_MOTION = "orbit"


def normalize_motion(value):
    """全站運動方式；不認得的值一律退回預設。"""
    motion = value.strip() if isinstance(value, str) else ""
    return motion if motion in MOTIONS else DEFAULT_MOTION


def normalize_layers(data):
    """整理單一元素的圖層設定。"""
    if not isinstance(data, dict):
        data = {}

    return {
        "nucleus": (data.get("nucleus") or "").strip(),
        "name_img": (data.get("name_img") or "").strip(),
    }


def serialize_layers(payload):
    """整理要寫進 DB 的圖層設定。只帶到的欄位才會更新。"""
    record = {}

    for field in ("nucleus", "name_img"):
        if field in payload:
            record[field] = (payload.get(field) or "").strip()

    return record


def resolve_orbit_particle(particles, slug):
    """挑出要繞行的粒子。

    沒設定、或設定的粒子已經被刪掉時，退回粒子清單的第一個（清單本身是
    依 order 排序的，第一個通常就是電子），這樣後台還沒選過也有東西可看。
    """
    if not particles:
        return None

    slug = (slug or "").strip()
    if slug:
        for p in particles:
            if p.get("slug") == slug:
                return p

    return particles[0]
