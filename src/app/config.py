"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3:8b", alias="OLLAMA_MODEL")
    temperature: float = Field(default=0.2, alias="TEMPERATURE")
    num_ctx: int = Field(default=4096, alias="NUM_CTX")

    trace_dir: Path = Field(default=Path("data/traces"), alias="TRACE_DIR")
    docs_dir: Path = Field(default=Path("data/docs"), alias="DOCS_DIR")
    memory_dir: Path = Field(default=Path("data/memory"), alias="MEMORY_DIR")

    mode: str = Field(default="hybrid", alias="MODE")
    enable_web: bool = Field(default=True, alias="ENABLE_WEB")
    enable_playwright: bool = Field(default=False, alias="ENABLE_PLAYWRIGHT")
    frontend_enabled: bool = Field(default=True, alias="FRONTEND_ENABLED")

    port: int = Field(default=8000, alias="PORT")

    def ensure_directories(self) -> None:
        """Make sure runtime directories exist."""
        for directory in (self.trace_dir, self.docs_dir, self.memory_dir):
            directory_path = Path(directory)
            directory_path.mkdir(parents=True, exist_ok=True)

    @property
    def mode_normalized(self) -> str:
        choices = {"offline", "web", "hybrid"}
        value = self.mode.lower()
        if value not in choices:
            return "hybrid"
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


settings: Settings = get_settings()
