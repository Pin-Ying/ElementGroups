"""在本機試 AI 的真實輸出，不需要 Firebase。

用途：填好 AI_API_KEY 之後想看看模型實際回什麼——長度、格式、有沒有把
整段用 ``` 包起來、有沒有寫多餘的開場白。這些只有真的打一次才知道。

為什麼不直接開後台試：本機的 backend/.env 沒有可用的 Firebase 憑證，
真後端起不來。額度計數要讀 Firebase，但組提示與呼叫模型都不用，所以這支
腳本只 import app.prompts 與 app.gemini，繞過整個資料庫。

也因此這裡的呼叫「不會」計入每日額度——線上的額度是記在 Firebase 的。
用它試不代表線上額度沒被用掉；反過來說，在這裡試也不會扣線上的計數。

用法（在 backend/ 底下）：

    python scripts/try_ai.py page-seo
    python scripts/try_ai.py group-archetype --direction "再冷一點"
    python scripts/try_ai.py page-content --draft "$(cat some.md)"

每個 kind 都有一組寫死的示範 context，改下面的 SAMPLES 就能試自己的內容。
"""

import argparse
import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

# app/__init__.py 會 import auth，auth 又 import firebase，於是光是
# `from app.config import ...` 就會去連 Firebase。先塞一個只有 __path__ 的
# 空 app 套件進 sys.modules，之後 import app.xxx 會被當成子模組直接載入，
# __init__.py 不會執行。
_pkg = types.ModuleType("app")
_pkg.__path__ = [os.path.join(_ROOT, "app")]
sys.modules.setdefault("app", _pkg)

from app.config import settings  # noqa: E402
from app.gemini import call_gemini  # noqa: E402
from app.prompts import (  # noqa: E402
    build_group_prompt,
    build_page_prompt,
    build_prompt,
    build_seo_prompt,
)

# 示範用的 context。element-story 在正式流程裡是後端自己去 Firebase 撈
# 整筆元素資料，這裡直接寫一份等價的假資料，才能不連資料庫就試。
SAMPLES = {
    "element-story": lambda draft, direction: build_prompt(
        {
            "Name": "氫",
            "Symbol": "H",
            "AtomicNumber": 1,
            "AtomicMass": "1.008",
            "GroupBlock": "nonmetal",
            "StandardState": "Gas",
        },
        draft=draft,
        direction=direction,
        group_info="所屬族：1A\n形象名稱：鹼金屬先鋒\n共同特色：外型輕盈、配色偏冷白。",
    ),
    "page-content": lambda draft, direction: build_page_prompt(
        "介紹週期表的讀法", draft=draft, direction=direction
    ),
    "group-archetype": lambda draft, direction: build_group_prompt(
        "7A",
        elements="F、Cl、Br、I、At、Ts",
        name="鹵素獵食鳥",
        draft=draft,
        direction=direction,
    ),
    "page-seo": lambda draft, direction: build_seo_prompt(
        "元素說明書",
        "能力值怎麼看\n\n每個元素都有六項能力，對應真實的物理化學性質。\n\n"
        ":::cards\n### 熔點 | K\n固體變成液體的溫度。\n:::",
        draft=draft,
        direction=direction,
    ),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(SAMPLES))
    parser.add_argument("--draft", default="", help="模擬編輯框裡已經有的內容")
    parser.add_argument("--direction", default="", help="風格／方向")
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="只印出提示，不呼叫模型（不需要 API key，也不花額度）",
    )
    args = parser.parse_args()

    prompt = SAMPLES[args.kind](args.draft, args.direction)

    if args.show_prompt:
        print(prompt)
        return 0

    if not settings.AI_API_KEY:
        print(
            "backend/.env 裡的 AI_API_KEY 是空的。\n"
            "填好之後再跑一次；只想看提示長怎樣的話加 --show-prompt。",
            file=sys.stderr,
        )
        return 1

    print(f"── 模型：{settings.AI_MODEL} ──", file=sys.stderr)
    text = call_gemini(prompt)

    # 這幾項就是要看的：有沒有被 ``` 包起來、有沒有多餘換行、實際多長
    print(f"── 輸出（{len(text)} 字，{text.count(chr(10)) + 1} 行）──", file=sys.stderr)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
