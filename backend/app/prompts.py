"""AI 提示的組裝。

從 ai.py 拆出來的理由：提示是 context 的純函式，不需要資料庫。原本和用量
計數放在同一個模組，而用量要讀 Firebase，於是「想看一下提示長怎樣」也得先
有一份可用的 Firebase 憑證——本機沒有憑證就完全試不了輸出。

拆開之後 ai.py 仍然是唯一的入口（額度、註冊表、呼叫），這裡只負責把字串
組出來，可以單獨 import、單獨測。
"""

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


def build_particle_title_prompt(name, description="", draft="", direction=""):
    """基本粒子的形象稱呼。要的是一句視覺描述，不是學名。"""
    parts = [
        "你是一個科普網站的美術設定，正在替基本粒子想一句形象稱呼。",
        "這個站把粒子畫成有個性的角色，形象稱呼就是一眼看見的樣子。",
        "",
        f"粒子：{name}",
    ]

    if description:
        parts += ["", "這顆粒子目前的介紹：", description]

    parts += [
        "",
        "撰寫要求：",
        "- 使用繁體中文，一句話，不超過 25 個字",
        "- 描述外觀與氣質，像「黑白相間、變化無常又長翅膀的小圓球」",
        "- 可以呼應這顆粒子真實的性質（電荷、質量、穩定性），但用形象的講法",
        "- 純文字，不要標點以外的符號、不要引號、不要換行",
        "- 只輸出這一句，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += ["", "站長目前寫的版本（請在此基礎上改寫）：", draft]

    return "\n".join(parts)


def build_particle_intro_prompt(name, title="", draft="", direction=""):
    """基本粒子的介紹段落。創作型，但要扣著真實物理。"""
    parts = [
        "你是一個科普網站的編輯，正在替基本粒子撰寫介紹。",
        "這個站把粒子畫成有個性的角色，但文字是旁白在介紹這個角色，"
        "不是角色自己說話。",
        "",
        f"粒子：{name}",
    ]

    if title:
        parts.append(f"站長已經定的形象稱呼：{title}")

    parts += [
        "",
        "撰寫要求：",
        "- 使用繁體中文，200 到 300 字，分成 2 至 3 段",
        "- 用第三人稱寫，不要用第一人稱扮演這顆粒子說話",
        "- 講清楚它是什麼、有什麼性質、在哪裡會遇到它",
        "- 語氣親切、適合一般讀者，可以呼應上面的形象稱呼",
        "- 物理事實要正確，寧可不寫也不要編",
        "- 只輸出介紹本文，不要下標題，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += [
            "",
            "站長目前已經寫了以下內容，請在保留原意的前提下延伸或潤飾，不要整段捨棄重寫：",
            draft,
        ]

    return "\n".join(parts)


def build_molecule_prompt(facts, draft="", direction=""):
    """分子的科普說明。有分子式與 IUPAC 名稱可以扣，最不容易寫歪的一種。"""
    parts = [
        "你是一個科普網站的編輯，正在替一個分子撰寫介紹。",
        "",
        "分子資料：",
    ]
    parts += [f"- {label}：{value}" for label, value in facts]

    parts += [
        "",
        "撰寫要求：",
        "- 使用繁體中文，兩到三段，每段三到四句",
        "- 講清楚它是什麼、有什麼性質、在生活或工業上哪裡會遇到",
        "- 扣著上面的分子式與名稱寫，不要寫成放諸四海皆準的空泛文字",
        "- 化學事實要正確，不確定的就不要寫",
        "- 語氣親切、適合一般讀者",
        "- 只輸出介紹本文，不要下標題，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += [
            "",
            "站長目前已經寫了以下內容，請在保留原意的前提下延伸或潤飾，不要整段捨棄重寫：",
            draft,
        ]

    return "\n".join(parts)


def build_site_description_prompt(title, subtitle="", draft="", direction=""):
    """全站的 SEO 描述。搜尋結果與社群分享都會顯示這一段。"""
    parts = [
        "你是一個元素週期表科普網站的編輯，正在寫整個網站的簡介。",
        "這段字會出現在搜尋結果、以及分享連結時的預覽卡片上。",
        "",
        f"網站標題：{title}",
    ]

    if subtitle:
        parts.append(f"副標題：{subtitle}")

    parts += [
        "",
        "這個站的內容：把元素週期表的每個元素當成有個性的角色來介紹，"
        "可以依化學性質、價電子等條件分組瀏覽，另外還有分子與基本粒子的圖鑑。",
        "",
        "撰寫要求：",
        "- 使用繁體中文，一到兩句，不超過 80 個字",
        "- 說明這個站在做什麼、對誰有用",
        "- 純文字，不要 Markdown、不要引號、不要換行",
        "- 只輸出這段描述，不要說明你在做什麼",
    ]

    if direction:
        parts += ["", f"額外的風格或方向要求：{direction}"]

    if draft:
        parts += ["", "站長目前寫的版本（請在此基礎上改寫）：", draft]

    return "\n".join(parts)
