from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Flask
    SECRET_KEY: str
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Firebase Admin SDK
    FIREBASE_PROJECT_ID: str
    FIREBASE_PRIVATE_KEY_ID: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_CLIENT_ID: str
    FIREBASE_STORAGE_BUCKET: str
    FIREBASE_STORAGE_ENABLED: bool = False
    FIREBASE_DATABASE_URL: str

    # 允許登入後台的帳號。以逗號分隔，可填 UID 或 email（大小寫不拘）。
    #
    # 為什麼需要：login() 只驗證「這組帳密在這個 Firebase 專案裡有效」，
    # 不驗證「這個人是不是站長」。Firebase Auth 的註冊是打 Google 的公開
    # 端點，只要 FIREBASE_API_KEY（依設計就不是機密），任何人建一個帳號
    # 就能登入後台。這裡是程式端的第二道鎖，不依賴主控台的設定。
    #
    # 留空＝不檢查（沿用舊行為），但每次登入都會印警告。
    # 用 `python scripts/list_auth_users.py` 可以查出自己的 UID。
    ADMIN_ACCOUNTS: str = ""

    # 後台是否顯示「用 Google 帳號登入」。
    #
    # 預設關閉，因為程式這邊無法得知你有沒有在 Firebase 主控台啟用 Google
    # 供應商——沒啟用就開這個開關，前台會出現一顆按下去只會噴錯的按鈕。
    #
    # 開啟前要做完三件事（見 issue #32）：
    #   1. Authentication → Sign-in method 啟用 Google 供應商
    #   2. Authentication → Settings → 授權網域加入 Render 的前端網域，
    #      漏掉的話線上按下去會被擋，而且錯誤訊息不會說是這個原因
    #   3. 確認 ADMIN_ACCOUNTS 已經設定 ← 最重要
    #
    # 第 3 點沒做的話，開這個功能會讓後台比現在更不安全：任何 Google 帳號
    # 都能完成 Firebase 的登入流程，Google 只證明「這個人是這個 email 的
    # 擁有者」，不判斷「這個人能不能進你的後台」。擋下來的是 ADMIN_ACCOUNTS，
    # 不是 Google。
    GOOGLE_LOGIN_ENABLED: bool = False

    # 帳號密碼登入。不填的話跟著 Google 登入連動：開了 Google 就關掉帳密。
    #
    # 為什麼要關：Firebase Auth 的 email／密碼註冊是打 Google 的公開端點，
    # 只要有 FIREBASE_API_KEY（依設計就不是機密）任何人都能建帳號。留著這
    # 條路，ADMIN_ACCOUNTS 就得一直當唯一那道鎖；關掉之後連「能不能通過
    # 第一關」都不成立了。
    #
    # 只把前端表單藏起來是不夠的——/api/auth/login 這支端點還在，繞過畫面
    # 直接打就行。所以這個開關是在後端擋，前端只是照著它決定要不要畫。
    #
    # **逃生門**：Google 那邊出狀況（供應商被停用、授權網域被改掉、帳號
    # 被鎖）時，把這個明確設成 true 就能立刻恢復帳密登入，不必改程式或
    # 重新部署前端。設成 false 則是強制關閉，連 Google 都沒開也一樣。
    PASSWORD_LOGIN_ENABLED: Optional[bool] = None

    @property
    def password_login_enabled(self) -> bool:
        """帳密登入現在到底開著沒。明確設定優先，否則與 Google 登入互斥。"""
        if self.PASSWORD_LOGIN_ENABLED is not None:
            return self.PASSWORD_LOGIN_ENABLED
        return not self.GOOGLE_LOGIN_ENABLED

    # Firebase Client (Pyrebase)
    FIREBASE_API_KEY: str
    FIREBASE_AUTH_DOMAIN: str
    FIREBASE_MESSAGING_SENDER_ID: str
    FIREBASE_APP_ID: str
    FIREBASE_MEASUREMENT_ID: str

    # AI 故事協助（選用）。沒設 AI_API_KEY 時整個功能不會啟用，
    # 前端也不會顯示相關按鈕。
    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    # Google 會讓舊型號退役，屆時 API 直接回 404。想固定在某個版本就在
    # .env 指定；不指定的話這個預設值要跟著更新
    AI_MODEL: str = "gemini-flash-latest"
    AI_DAILY_LIMIT: int = 50
    # 思考型模型會先花掉一部分輸出預算，太低會讓正文被截斷
    AI_MAX_OUTPUT_TOKENS: int = 4096

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
