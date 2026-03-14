from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://ainote:ainote@db:5432/ainote_community"
    JWT_SECRET: str = "change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OPENAI_API_KEY: str = ""
    APP_BASE_URL: str = "http://localhost:3000"
    DATA_DIR: str = "./data"
    NSX_IMPORTS_PATH: str = "./data/nsx_imports"
    NSX_IMAGES_PATH: str = "./data/nsx_images"
    SYNOLOGY_URL: str = ""
    SYNOLOGY_USER: str = ""
    SYNOLOGY_PASSWORD: str = ""
    SYNOLOGY_VERIFY_SSL: bool = False
    GITHUB_FEEDBACK_REPO: str = ""
    GITHUB_FEEDBACK_TOKEN: str = ""
    GITHUB_FEEDBACK_LABELS: str = "community-feedback,ainote-community"

    @property
    def data_dir(self) -> Path:
        return Path(self.DATA_DIR).resolve()

    @property
    def state_file(self) -> Path:
        return self.data_dir / "community_state.json"

    @property
    def snapshots_dir(self) -> Path:
        return self.data_dir / "snapshots"

    @property
    def feedback_assets_dir(self) -> Path:
        return self.data_dir / "feedback_assets"

    @property
    def nsx_imports_dir(self) -> Path:
        return Path(self.NSX_IMPORTS_PATH).resolve()

    @property
    def nsx_images_dir(self) -> Path:
        return Path(self.NSX_IMAGES_PATH).resolve()

    @property
    def github_feedback_labels(self) -> list[str]:
        return [label.strip() for label in self.GITHUB_FEEDBACK_LABELS.split(",") if label.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
