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
    AI_MODEL: str = "gemini-2.0-flash"
    AI_DAILY_LIMIT: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
