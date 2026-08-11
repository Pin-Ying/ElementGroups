"""呼叫 Gemini。

和 ai.py 分開的理由與 prompts.py 相同：送出提示、解讀回應只需要
settings，不需要資料庫。額度計數（要讀 Firebase）留在 ai.py。
"""

import requests

from app.config import settings

REQUEST_TIMEOUT = 30

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def call_gemini(prompt):
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
                "請調高 AI_MAX_OUTPUT_TOKENS，或改用非思考型模型"
            )
        raise RuntimeError(f"AI 回傳了空白內容（finishReason: {finish_reason or '未知'}）")

    if finish_reason == "MAX_TOKENS":
        raise RuntimeError(
            f"AI 回應在寫完之前就達到輸出上限（目前 {settings.AI_MAX_OUTPUT_TOKENS} tokens），"
            "內容不完整。請調高 AI_MAX_OUTPUT_TOKENS 後重試"
        )

    return text
