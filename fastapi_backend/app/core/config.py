from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hint Generation System"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Trusted hosts for Host header validation
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./hint_system.db"
    
    # AI/LLM Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "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")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # LangSmith Configuration
    LANGSMITH_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "hg")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_TRACING_V2: bool = (
        os.getenv("LANGSMITH_TRACING_V2", "false").lower() == "true" or
        os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    )
    
    # Model Configuration
    DEFAULT_MODEL: str = "deepseek/deepseek-r1-0528-qwen3-8b:free"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "fastapi.log"
    
    # Hint System Configuration
    MAX_HINT_LEVEL: int = 5
    AUTO_TRIGGER_TIMEOUT: int = 300  # 5 minutes in seconds
    MAX_FAILED_ATTEMPTS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 