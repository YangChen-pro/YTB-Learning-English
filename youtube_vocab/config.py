"""Central configuration loaded from CLI arguments and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def default_database_path() -> Path:
    override = os.getenv("YTVOCAB_DB_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "share" / "ytvocab" / "ytvocab.db"


@dataclass(frozen=True, slots=True)
class Settings:
    model: str
    api_key: str | None
    database_path: Path
    base_url: str = "https://api.deepseek.com"
    spacy_model: str = "en_core_web_sm"
    ytdlp_cookies_browser: str | None = None
    ytdlp_js_runtime: str | None = None
    ytdlp_remote_components: str | None = None

    @classmethod
    def from_env(cls, *, model: str | None = None, database_path: Path | None = None) -> Settings:
        load_dotenv()
        selected_model = model or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-flash"
        return cls(
            model=selected_model,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            database_path=database_path or default_database_path(),
            ytdlp_cookies_browser=os.getenv("YTVOCAB_YTDLP_COOKIES_BROWSER") or None,
            ytdlp_js_runtime=os.getenv("YTVOCAB_YTDLP_JS_RUNTIME") or None,
            ytdlp_remote_components=os.getenv("YTVOCAB_YTDLP_REMOTE_COMPONENTS") or None,
        )
