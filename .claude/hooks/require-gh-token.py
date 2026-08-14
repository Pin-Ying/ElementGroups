#!/usr/bin/env python3
"""擋下沒有帶 GitHub token 的 gh 呼叫。

為什麼需要這個：`gh` 找不到 token 時會退回 ~/.config/gh/hosts.yml 裡的預設
帳號，於是留言、開 PR 就用了別人的身分發出去——而且完全沒有警告。這種錯誤
只有事後從 issue 上的頭像才看得出來。

擋的條件：指令裡叫了 gh，但既沒有行內的 GH_TOKEN=／GITHUB_TOKEN=，環境裡
也沒有。環境變數由 .claude/settings.local.json 的 env 注入。

退出碼 2 = 擋下並把訊息回給 Claude（見 Claude Code 的 hook 規格）。
"""

import json
import os
import re
import sys

# 只認「指令開頭或管線／分號之後」的 gh，避免 `grep gh` 這種誤判
GH_CALL = re.compile(r"(^|[|;&]|\n)\s*(\w+=\S+\s+)*gh\s", re.M)
INLINE_TOKEN = re.compile(r"\b(GH_TOKEN|GITHUB_TOKEN)=")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # 讀不到就不要擋，hook 壞掉不該讓整個工作停擺

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not GH_CALL.search(command):
        return 0
    if INLINE_TOKEN.search(command):
        return 0
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        return 0

    sys.stderr.write(
        "擋下了：這個 gh 指令沒有帶 token，會掉回 ~/.config/gh 的預設帳號，"
        "用錯身分發言。\n"
        "這個專案一律用 elandcelinelu，請改成：\n"
        "  GH_TOKEN=$(tr -d '\\n\\r ' < github-token.txt) gh ...\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
