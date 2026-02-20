from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Flask
    SECRET_KEY: str
    DATABASE_URI: str = "sqlite:///elementGroups.db"
    PORT: int = 8000

    # Firebase Admin SDK
    FIREBASE_PROJECT_ID: str
    FIREBASE_PRIVATE_KEY_ID: str
    FIREBASE_PRIVATE_KEY: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_CLIENT_ID: str
    FIREBASE_STORAGE_BUCKET: str
    FIREBASE_DATABASE_URL: str

    # Firebase Client (Pyrebase)
    FIREBASE_API_KEY: str
    FIREBASE_AUTH_DOMAIN: str
    FIREBASE_MESSAGING_SENDER_ID: str
    FIREBASE_APP_ID: str
    FIREBASE_MEASUREMENT_ID: str

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
