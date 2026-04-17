from functools import lru_cache
from app.core.settings.app import AppSettings

@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings() # type: ignore

settings = get_settings()