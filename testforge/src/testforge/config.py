"""TestForge configuration via Pydantic Settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TESTFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # LLM
    llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    llm_model: str = "gpt-4o"
    llm_api_key: str = ""
    llm_base_url: str | None = None
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    # Execution
    sandbox_mode: Literal["subprocess", "docker"] = "subprocess"
    test_timeout_seconds: int = 60
    max_parallel_tests: int = 4

    # Paths
    workspace_dir: Path = Field(default_factory=lambda: Path.cwd() / ".testforge")
    generated_tests_dir: Path | None = None

    # Database
    db_path: Path | None = None

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    streamlit_port: int = 8501

    # Observer (Phase 2)
    proxy_port: int = 8080

    def get_db_path(self) -> Path:
        if self.db_path:
            return self.db_path
        return self.workspace_dir / "testforge.db"

    def get_generated_tests_dir(self) -> Path:
        if self.generated_tests_dir:
            return self.generated_tests_dir
        return self.workspace_dir / "generated_tests"

    def ensure_dirs(self) -> None:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.get_generated_tests_dir().mkdir(parents=True, exist_ok=True)


settings = Settings()
