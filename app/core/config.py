from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FRONTEND_URL: str = "http://localhost:3000"

    # Security settings
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5

    # Email settings
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "BridgeAI"
    # AI settings - Groq
    GROQ_API_KEY: str
    ANTHROPIC_API_KEY: str = ""  # Keep for backward compatibility but make optional

    # LLM Model Configuration
    # Default model for all AI operations (can be overridden per component)
    # Available Groq models:
    # - llama-3.3-70b-versatile (Powerful - best for reasoning & complex tasks)
    # - llama-3.1-8b-instant (Fast & efficient)
    # - mixtral-8x7b-32768 (Strong open-weight model)
    LLM_DEFAULT_MODEL: str = "llama-3.3-70b-versatile"

    # Component-specific model configurations
    # Clarification needs good reasoning - use Llama 3.3 70B
    LLM_CLARIFICATION_MODEL: str = "llama-3.3-70b-versatile"
    LLM_CLARIFICATION_TEMPERATURE: float = 0.3
    LLM_CLARIFICATION_MAX_TOKENS: int = 2048

    # Template Filler needs structured extraction - use Llama 3.3 70B
    LLM_TEMPLATE_FILLER_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPLATE_FILLER_TEMPERATURE: float = 0.2
    LLM_TEMPLATE_FILLER_MAX_TOKENS: int = 4096

    # Suggestions can use Llama 3.1 8B for speed and cost savings
    LLM_SUGGESTIONS_MODEL: str = "llama-3.1-8b-instant"
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

    GROQ_API_KEY: str
    google_client_id: str
    google_client_secret: str

settings = Settings()
