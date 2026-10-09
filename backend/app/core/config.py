from __future__ import annotations
import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "opsagent-development-key-change-in-production"

    # Server Ports & Hosts
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ERP Configuration
    MOCK_ERP_HOST: str = "0.0.0.0"
    MOCK_ERP_PORT: int = 8001
    ERP_BASE_URL: str = "http://localhost:8001/api/v1"
    ERP_API_KEY: str = "mock-erp-secret-key-2026"

    # Database URLs
    DATABASE_URL: str = "postgresql+psycopg2://opsagent:opsagent_password@localhost:5432/opsagent_db"
    DATABASE_RO_URL: str = "postgresql+psycopg2://opsagent_ro:opsagent_ro_password@localhost:5432/opsagent_db"

    # LLM Providers & Models
    DEFAULT_LLM_PROVIDER: Literal["groq", "openai", "anthropic"] = "groq"
    ROUTER_MODEL: str = "llama-3.1-8b-instant"
    SYNTHESIS_MODEL: str = "llama-3.3-70b-versatile"

    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # RAG Settings
    VECTOR_STORE_TYPE: Literal["chroma", "pgvector"] = "chroma"
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    CHUNK_SIZE_TOKENS: int = 650
    CHUNK_OVERLAP_TOKENS: int = 80

    # Microsoft 365 Mock / Graph API
    M365_USE_MOCK: bool = True
    M365_TENANT_ID: Optional[str] = None
    M365_CLIENT_ID: Optional[str] = None
    M365_CLIENT_SECRET: Optional[str] = None

    # Guardrails & Observability
    GUARDRAILS_ENABLED: bool = True
    MASK_PII_ENABLED: bool = True
    PROMPT_INJECTION_THRESHOLD: float = 0.75
    DEFAULT_USER_ROLE: Literal["staff", "manager"] = "staff"


settings = Settings()
