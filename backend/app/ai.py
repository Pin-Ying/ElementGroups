"""AI 故事協助（選用功能）。

沒有設定 `AI_API_KEY` 時 `is_enabled()` 回傳 False，前端據此完全隱藏
相關介面，其餘功能不受影響。

呼叫次數以 UTC 日期為單位記在 Realtime DB 的 `_ai_usage` node，避免
不小心把免費額度用光。
"""

import datetime

import requests

from app.config import settings
from app.firebase import fdb

USAGE_NODE = "_ai_usage"
REQUEST_TIMEOUT = 30

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


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


def build_prompt(element, draft="", direction="", reference="", group_info=""):
    """組出給模型的提示。

    element 是 periodic_table 裡該元素的整筆資料，帶進去讓內容扣著這個
    元素講，而不是產生放諸四海皆準的空泛文字。
    """
    facts = []
    for label, key in [
        ("名稱", "Name"),
        ("符號", "Symbol"),
        ("原子序", "AtomicNumber"),
        ("原子量", "AtomicMass"),
        ("分類", "GroupBlock"),
        ("常溫狀態", "StandardState"),
        ("電子組態", "ElectronConfiguration"),
        ("常見氧化態", "OxidationStates"),
        ("發現年份", "YearDiscovered"),
        ("熔點(K)", "MeltingPoint"),
        ("沸點(K)", "BoilingPoint"),
    ]:
        value = element.get(key)
        if value:
            facts.append(f"- {label}：{value}")

    parts = [
        "你是一個科普網站的編輯，正在替元素週期表的每個元素撰寫簡短的介紹故事。",
        "",
        "請根據以下元素資料撰寫：",
        "\n".join(facts),
        "",
        "撰寫要求：",
        "- 使用繁體中文",
        "- 200 到 300 字，分成 2 至 3 段",
        "- 語氣親切、適合一般讀者，可以帶入生活中的例子或有趣的歷史",
        "- 內容必須符合上面的元素資料，不要杜撰數據",
        "- 只輸出故事內文，不要加標題、不要用 Markdown 語法、不要說明你在做什麼",
    ]

    if group_info:
        parts += [
            "",
            "這個元素所屬的族有整體的形象設定，撰寫時請自然地呼應這個形象"
            "（不必逐字引用）：",
            group_info,
        ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if reference:
        parts += ["", "請參考以下補充資料：", reference]

    if draft:
        parts += [
            "",
            "使用者目前已經寫了以下內容，請在保留原意與既有語氣的前提下延伸或潤飾，"
            "不要整段捨棄重寫：",
            draft,
        ]

    return "\n".join(parts)


def _call_gemini(prompt):
    url = GEMINI_ENDPOINT.format(model=settings.AI_MODEL)
    response = requests.post(
        url,
        params={"key": settings.AI_API_KEY},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                # 一段 300 字的中文約 400~600 tokens，但具備思考能力的模型
                # 會先花掉一部分預算，額度抓寬一點才不會把正文切斷
                "maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS,
            },
        },
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code != 200:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except Exception:
            detail = response.text[:200]
        raise RuntimeError(f"Gemini API 回應 {response.status_code}：{detail}")

    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        # 例如被安全設定擋下時不會有 candidates
        reason = data.get("promptFeedback", {}).get("blockReason", "沒有回傳內容")
        raise RuntimeError(f"AI 沒有產生內容（{reason}）")

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts") or []
    # 具備思考能力的模型會把思考過程也放在 parts 裡並標記 thought=True，
    # 那不是要給使用者看的內容，必須濾掉，否則會拼出前後不連貫的段落
    text = "".join(
        p.get("text", "") for p in parts if not p.get("thought")
    ).strip()

    finish_reason = candidate.get("finishReason", "")
    if not text:
        if finish_reason == "MAX_TOKENS":
            raise RuntimeError(
                "AI 的輸出額度用在思考過程上，沒有產生正文。"
                "請調高 AI_MAX_OUTPUT_TOKENS，或改用非思考型模型（例如 gemini-2.0-flash）"
            )
        raise RuntimeError(f"AI 回傳了空白內容（finishReason: {finish_reason or '未知'}）")

    if finish_reason == "MAX_TOKENS":
        raise RuntimeError(
            f"AI 回應在寫完之前就達到輸出上限（目前 {settings.AI_MAX_OUTPUT_TOKENS} tokens），"
            "內容不完整。請調高 AI_MAX_OUTPUT_TOKENS 後重試"
        )

    return text


def build_page_prompt(topic, draft="", direction=""):
    """頁面內容的提示。與元素故事不同：輸出 Markdown，並支援本站自訂區塊。"""
    parts = [
        "你是一個元素週期表科普網站的編輯，正在撰寫網站的說明頁面。",
        "",
        f"頁面主題：{topic}",
        "",
        "撰寫要求：",
        "- 使用繁體中文",
        "- 使用 Markdown 語法（# 標題、**粗體**、- 清單、--- 分隔線）",
        "- 本站另外支援三種區塊語法，適合時可以使用：",
        "  :::cards 區塊：每個 ### 標題一張卡片，標題可用 | 分隔附註，適合並列的名詞解釋",
        "  :::note 區塊：提示或補充說明",
        "  （以 ::: 開始、以 ::: 結尾）",
        "- 內容正確、語氣親切、適合一般讀者",
        "- 只輸出頁面內文，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += [
            "",
            "使用者目前已經寫了以下內容，請在保留原意與既有結構的前提下延伸或潤飾，"
            "不要整段捨棄重寫：",
            draft,
        ]

    return "\n".join(parts)


def build_group_prompt(key, elements, name="", draft="", direction=""):
    """主族形象的提示。創作型：要產生的是同族共用的設計特色，不是化學知識。"""
    parts = [
        "你是一個元素週期表科普網站的美術設定，正在為週期表的一個族設計共同形象。",
        "這個站把每個元素當成有個性的角色，同一族的角色共享一組設計語彙。",
        "",
        f"族：{key}",
    ]

    if elements:
        parts.append(f"這一族的元素：{elements}")
    if name:
        parts.append(f"站長已經定的形象名稱：{name}")

    parts += [
        "",
        "撰寫要求：",
        "- 使用繁體中文，寫成一段連貫的說明，不要條列",
        "- 內容是「共同的設計特色」：外型輪廓、配色傾向、氣質、常見配件之類",
        "- 可以呼應這一族真實的化學性質（活性、價電子、常見用途），但重點是形象",
        "- 三到五句，讓站長之後畫每個元素時有依據",
        "- 只輸出這段說明，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += [
            "",
            "站長目前已經寫了以下設定，請在保留原意的前提下延伸或潤飾，不要整段捨棄重寫：",
            draft,
        ]

    return "\n".join(parts)


def build_seo_prompt(title, content, draft="", direction=""):
    """頁面 SEO 描述的提示。摘要型：從既有內容濃縮，不要自己發明。"""
    parts = [
        "你是一個元素週期表科普網站的編輯，正在為一個頁面寫搜尋結果會顯示的描述。",
        "",
        f"頁面標題：{title}",
    ]

    if content:
        parts += ["", "頁面內容：", content]
    else:
        parts += ["", "（這個頁面還沒有內容，請只依標題推測這頁在講什麼。）"]

    parts += [
        "",
        "撰寫要求：",
        "- 使用繁體中文，一句話，不超過 70 個字",
        "- 說明這一頁在講什麼，讓人在搜尋結果看到就知道要不要點進來",
        "- 只根據上面的內容濃縮，不要自己補沒提到的事",
        "- 純文字，不要 Markdown、不要引號、不要換行",
        "- 只輸出這一句描述，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += ["", "站長目前寫的版本（請在此基礎上改寫）：", draft]

    return "\n".join(parts)


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


SUGGEST_KINDS = {
    "element-story": _element_story_prompt,
    "page-content": _page_content_prompt,
    "group-archetype": _group_archetype_prompt,
    "page-seo": _page_seo_prompt,
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

    text = _call_gemini(builder(context or {}, draft, direction))
    _increment_usage()
    return text, used + 1, limit
