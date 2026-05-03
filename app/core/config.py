from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:3000"

    # Google Auth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # Security settings
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5

    # Email settings (Resend API)
    RESEND_API_KEY: str
    EMAIL_FROM_ADDRESS: str = "admin@bridge-ai.dev"
    EMAIL_FROM_NAME: str = "BridgeAI"
    # AI settings
    GROQ_API_KEY: str = ""  # Optional if using Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Encryption key for user API keys at rest (Fernet symmetric encryption)
    ENCRYPTION_KEY: str = ""

    # LLM Model Configuration
    LLM_DEFAULT_MODEL: str = "llama-3.3-70b-versatile"

    # Component-specific model configurations
    LLM_CLARIFICATION_MODEL: str = "llama-3.3-70b-versatile"
    LLM_CLARIFICATION_TEMPERATURE: float = 0.3
    LLM_CLARIFICATION_MAX_TOKENS: int = 2048

    LLM_TEMPLATE_FILLER_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPLATE_FILLER_TEMPERATURE: float = 0.2
    LLM_TEMPLATE_FILLER_MAX_TOKENS: int = 4096

    LLM_SUGGESTIONS_MODEL: str = "llama3-8b-8192"
    LLM_SUGGESTIONS_TEMPERATURE: float = 0.7
    LLM_SUGGESTIONS_MAX_TOKENS: int = 2000

    # ChromaDB settings (vector database for semantic search)
    CHROMA_SERVER_HOST: str = "localhost"
    CHROMA_SERVER_HTTP_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "project_memories"
    CHROMA_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # 384-dimensional embeddings
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    chroma_db_path: str = Field(default="./chroma_db")
    embedding_model: str = Field(default="openai")


settings = Settings()
