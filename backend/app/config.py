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
