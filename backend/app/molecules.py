"""分子資料。

存在 Realtime DB 的 `_molecules/{slug}`。slug 取自 IUPAC 名稱，因為那是
分子的標準命名，也讓網址穩定；顯示名稱另存，可以用中文或俗名。

新增時會先到 PubChem 查一次，查到就自動帶入分子式、分子量等資料；查不到
（PubChem 回 404）則轉為手動填寫，不擋使用者建立冷門或自訂的分子。
"""

import re

MOLECULES_NODE = "_molecules"

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# 分子式解析：連續的元素符號與數量，支援括號群組
_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)|(\()|(\))(\d*)")


def normalize_slug(raw):
    """轉成網址友善的 slug。IUPAC 名稱常含括號、逗號與上標，一併清掉。"""
    slug = (raw or "").strip().lower()
    slug = re.sub(r"[\[\]\(\)\{\}]", " ", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if not slug or not SLUG_PATTERN.match(slug):
        return None
    return slug[:80]


def elements_in_formula(formula):
    """從分子式取出用到的元素符號，供分子與元素頁互相連結。"""
    if not formula:
        return []
    seen = []
    for match in re.finditer(r"[A-Z][a-z]?", str(formula)):
        symbol = match.group()
        if symbol not in seen:
            seen.append(symbol)
    return seen


def normalize_molecule(slug, data):
    if not isinstance(data, dict):
        return None

    formula = (data.get("formula") or "").strip()
    return {
        "slug": slug,
        "name": (data.get("name") or "").strip() or slug,
        "iupac_name": (data.get("iupac_name") or "").strip(),
        "formula": formula,
        "weight": (data.get("weight") or "").strip(),
        "smiles": (data.get("smiles") or "").strip(),
        "cid": data.get("cid") or None,
        "description": data.get("description") or "",
        # 自訂代表圖；沒有就用 PubChem 的結構圖
        "img_data": (data.get("img_data") or "").strip(),
        # 建構器的節點結構，讓之後可以再編輯
        "nodes": data.get("nodes") if isinstance(data.get("nodes"), list) else [],
        "elements": data.get("elements") if isinstance(data.get("elements"), list)
                    else elements_in_formula(formula),
        "source": (data.get("source") or "manual").strip(),
        "published": bool(data.get("published", True)),
        "updated_at": data.get("updated_at") or "",
    }


def normalize_molecules(data, include_drafts=False):
    if not isinstance(data, dict):
        return []

    items = []
    for slug, raw in data.items():
        molecule = normalize_molecule(slug, raw)
        if not molecule:
            continue
        if not include_drafts and not molecule["published"]:
            continue
        items.append(molecule)

    # 最近更新的排前面，沒有時間戳的排後面
    items.sort(key=lambda m: m["updated_at"] or "", reverse=True)
    return items


def serialize_molecule(payload):
    """整理要寫進 DB 的分子資料。回傳 (slug, record) 或 (None, 錯誤訊息)。"""
    name = (payload.get("name") or "").strip()
    iupac = (payload.get("iupac_name") or "").strip()

    # slug 優先取 IUPAC 名稱；沒有就退回顯示名稱
    slug = normalize_slug(payload.get("slug") or iupac or name)
    if not slug:
        return None, "無法從名稱產生網址代稱，請改用英文名稱或自行填寫"
    if not name and not iupac:
        return None, "請填寫分子名稱"

    formula = (payload.get("formula") or "").strip()
    nodes = payload.get("nodes") if isinstance(payload.get("nodes"), list) else []

    return slug, {
        "name": name or iupac,
        "iupac_name": iupac,
        "formula": formula,
        "weight": (payload.get("weight") or "").strip(),
        "smiles": (payload.get("smiles") or "").strip(),
        "cid": payload.get("cid") or None,
        "description": payload.get("description") or "",
        "img_data": (payload.get("img_data") or "").strip(),
        "nodes": nodes,
        "elements": elements_in_formula(formula),
        "source": (payload.get("source") or "manual").strip(),
        "published": bool(payload.get("published", True)),
    }
