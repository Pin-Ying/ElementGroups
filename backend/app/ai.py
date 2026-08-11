"""AI 故事協助（選用功能）。

沒有設定 `AI_API_KEY` 時 `is_enabled()` 回傳 False，前端據此完全隱藏
相關介面，其餘功能不受影響。

呼叫次數以 UTC 日期為單位記在 Realtime DB 的 `_ai_usage` node，避免
不小心把免費額度用光。
"""

import datetime

from app.config import settings
from app.firebase import fdb
from app.gemini import call_gemini
from app.prompts import (
    build_group_prompt,
    build_molecule_prompt,
    build_page_prompt,
    build_particle_intro_prompt,
    build_particle_title_prompt,
    build_prompt,
    build_seo_prompt,
    build_site_description_prompt,
)

USAGE_NODE = "_ai_usage"


def is_enabled():
    return bool(settings.AI_API_KEY)


def _today_key():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def get_usage():
    """回傳 (今日已用次數, 每日上限)。"""
    try:
        used = fdb.child(USAGE_NODE).child(_today_key()).get() or 0
    except Exception as e:
        print(f"Failed to read AI usage: {e}")
        used = 0
    return int(used), settings.AI_DAILY_LIMIT


def _increment_usage():
    key = _today_key()
    try:
        used = fdb.child(USAGE_NODE).child(key).get() or 0
        fdb.child(USAGE_NODE).child(key).set(int(used) + 1)
    except Exception as e:
        print(f"Failed to update AI usage: {e}")


# ── 建議用途的註冊表 ──────────────────────────────────────────────
#
# key 就是前後端之間唯一的約定。後端只管「這個 kind 的提示怎麼組」，
# 前端只管「這個 kind 要收哪些輸入」——提示必須在伺服器端（API key 在
# 這裡），輸入介面必須在瀏覽器端，這個分工是本質上的，不是重複。
#
# 要新增一個 AI 用途：這裡補一個 builder，前端 utils/aiKinds.js 補對應
# 的欄位定義。不必再寫端點，也不必再做一組面板。
#
# builder 收到 (context, draft, direction)，context 是前端送來的原始
# 物件，各自決定怎麼解讀、需要時自己去查資料。

def _element_story_prompt(context, draft, direction):
    from app.firebase import get_element_by_symbol, show_fdb
    from app.groups import GROUPS_NODE, normalize_group, group_key_for, has_content

    symbol = (context.get("symbol") or "").strip()
    element = get_element_by_symbol(symbol)
    if not element:
        raise ValueError(f"找不到元素 {symbol}")

    # 勾選帶入主族形象時，後端自己查該元素所屬族的設定（issue #16）
    group_info = ""
    if context.get("include_group"):
        key = group_key_for(element.get("AtomicNumber"))
        if key:
            group = normalize_group(key, show_fdb(f"{GROUPS_NODE}/{key}"))
            if has_content(group):
                pieces = [f"所屬族：{key}"]
                if group["name"]:
                    pieces.append(f"形象名稱：{group['name']}")
                if group["description"]:
                    pieces.append(f"共同特色：{group['description']}")
                group_info = "\n".join(pieces)

    return build_prompt(
        element,
        draft=draft,
        direction=direction,
        reference=(context.get("reference") or "").strip(),
        group_info=group_info,
    )


def _page_content_prompt(context, draft, direction):
    topic = (context.get("topic") or "").strip()
    if not topic:
        raise ValueError("請先描述頁面主題")
    return build_page_prompt(topic, draft=draft, direction=direction)


def _group_archetype_prompt(context, draft, direction):
    from app.groups import GROUP_KEYS

    key = (context.get("key") or "").strip()
    if key not in GROUP_KEYS:
        raise ValueError(f"不認得的族：{key or '（未指定）'}")

    # 元素清單由前端帶入。族與元素的對照兩邊都有（groups.py 的 _POSITION 與
    # periodicTableGroups.js），但符號本身只在 periodic_table 節點裡，為了
    # 一個提示去整包讀那個節點正是拖垮 /elements/seo 的那件事。
    return build_group_prompt(
        key,
        elements=(context.get("elements") or "").strip(),
        name=(context.get("name") or "").strip(),
        draft=draft,
        direction=direction,
    )


def _page_seo_prompt(context, draft, direction):
    title = (context.get("title") or "").strip()
    if not title:
        raise ValueError("請先填頁面標題")

    # 內容太長沒有意義，描述只有一句話；截斷也省 token
    content = (context.get("content") or "").strip()[:4000]
    return build_seo_prompt(title, content, draft=draft, direction=direction)


def _particle_title_prompt(context, draft, direction):
    name = (context.get("name") or "").strip()
    if not name:
        raise ValueError("請先填粒子名稱")
    return build_particle_title_prompt(
        name,
        description=(context.get("description") or "").strip(),
        draft=draft,
        direction=direction,
    )


def _particle_intro_prompt(context, draft, direction):
    name = (context.get("name") or "").strip()
    if not name:
        raise ValueError("請先填粒子名稱")
    return build_particle_intro_prompt(
        name,
        title=(context.get("title") or "").strip(),
        draft=draft,
        direction=direction,
    )


# 分子表單上有一堆欄位，但站長不見得每個都填。只把有值的帶進提示，
# 空欄位列成「- 分子量：」只會讓模型以為那是個未知數而去猜
_MOLECULE_FACTS = (
    ("顯示名稱", "name"),
    ("IUPAC 名稱", "iupac_name"),
    ("分子式", "formula"),
    ("分子量", "weight"),
    ("分類", "category"),
    ("SMILES", "smiles"),
)


def _molecule_prompt(context, draft, direction):
    facts = [
        (label, str(context.get(key)).strip())
        for label, key in _MOLECULE_FACTS
        if str(context.get(key) or "").strip()
    ]
    if not facts:
        raise ValueError("請先填分子名稱或分子式")
    return build_molecule_prompt(facts, draft=draft, direction=direction)


def _site_description_prompt(context, draft, direction):
    title = (context.get("title") or "").strip()
    if not title:
        raise ValueError("請先填網站標題")
    return build_site_description_prompt(
        title,
        subtitle=(context.get("subtitle") or "").strip(),
        draft=draft,
        direction=direction,
    )


SUGGEST_KINDS = {
    "element-story": _element_story_prompt,
    "page-content": _page_content_prompt,
    "group-archetype": _group_archetype_prompt,
    "page-seo": _page_seo_prompt,
    "particle-title": _particle_title_prompt,
    "particle-intro": _particle_intro_prompt,
    "molecule": _molecule_prompt,
    "site-description": _site_description_prompt,
}


def suggest(kind, context=None, draft="", direction=""):
    """產生一則建議。回傳 (內容, 今日已用, 上限)。

    所有用途共用的前置檢查（是否啟用、每日額度、provider）都收在這裡，
    各用途只負責把提示組出來。
    """
    builder = SUGGEST_KINDS.get(kind)
    if not builder:
        raise ValueError(f"不認得的建議類型：{kind}")

    if not is_enabled():
        raise RuntimeError("AI 功能未啟用")

    used, limit = get_usage()
    if limit > 0 and used >= limit:
        raise RuntimeError(f"今日 AI 呼叫已達上限（{limit} 次），請明天再試")

    if settings.AI_PROVIDER != "gemini":
        raise RuntimeError(f"尚未支援的 AI_PROVIDER：{settings.AI_PROVIDER}")

    text = call_gemini(builder(context or {}, draft, direction))
    _increment_usage()
    return text, used + 1, limit
