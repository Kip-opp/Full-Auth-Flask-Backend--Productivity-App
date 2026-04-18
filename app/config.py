import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///todo.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AI_PROVIDER = os.getenv("AI_PROVIDER", "grok")
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
    XAI_MODEL = os.getenv("XAI_MODEL", "grok-4-1-fast-non-reasoning")