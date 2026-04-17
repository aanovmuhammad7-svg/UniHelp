import logging
import sys
from typing import Any, Dict, Literal, Tuple

from loguru import logger
from pydantic import PostgresDsn, RedisDsn, SecretStr, field_validator

from app.core.logging import InterceptHandler
from app.core.settings.base import BaseAppSettings


class AppSettings(BaseAppSettings):
    environment: Literal["development", "staging", "production", "test"] = "development"

    # FastAPI settings
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "UniHelp API"
    version: str = "0.1.0"

    # PostgreSQL
    database_url: PostgresDsn
    connection_count: int
    additional_connections: int

    # Redis
    redis_url: RedisDsn
    redis_max_connections: int

    # Telegram bot
    telegram_bot_token: SecretStr
    telegram_parse_mode: str = "HTML"

    # OpenAI
    openai_api_key: SecretStr
    openai_model: str = "gpt-4.1-mini"
    openai_max_tokens: int = 700
    openai_timeout_seconds: float = 15.0

    # Assistant behavior
    assistant_name: str = "UniHelp"
    assistant_system_prompt: str = (
        "Ты дружелюбный помощник для первокурсника. "
        "Помогай разобраться с учебой, расписанием, адаптацией, общением с преподавателями, "
        "оформлением документов и повседневными вопросами студенческой жизни. "
        "Отвечай понятно, спокойно и по делу. Если данных не хватает, сначала уточни детали. "
        "Не выдумывай факты про конкретный вуз: если информация зависит от университета, "
        "прямо скажи об этом и предложи, что нужно уточнить."
    )
    chat_history_limit: int = 10

    # Logging
    logging_level: int = logging.INFO
    loggers: Tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")

    # Rate limiting
    enable_rate_limiter: bool

    @property
    def fastapi_kwargs(self) -> Dict[str, Any]:
        return {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "openapi_prefix": self.openapi_prefix,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
        }

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, value: object) -> str:
        if value is None:
            return "development"

        normalized = str(value).strip().lower()
        aliases = {
            "dev": "development",
            "development": "development",
            "local": "development",
            "stage": "staging",
            "staging": "staging",
            "prod": "production",
            "production": "production",
            "release": "production",
            "test": "test",
            "testing": "test",
        }
        if normalized not in aliases:
            raise ValueError("environment must be one of development, staging, production, test")
        return aliases[normalized]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        normalized = str(value).strip().lower()
        truthy = {"1", "true", "yes", "on", "debug"}
        falsy = {"0", "false", "no", "off", "release", "prod", "production"}

        if normalized in truthy:
            return True
        if normalized in falsy:
            return False

        raise ValueError("debug must be a boolean-like value")


    def configure_logging(self) -> None:
        logging.getLogger().handlers = [InterceptHandler()]

        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
            uvicorn_logger = logging.getLogger(logger_name)
            uvicorn_logger.handlers = [InterceptHandler()]
            uvicorn_logger.propagate = False

        logger.remove()
        logger.add(
            sys.stdout,
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level:<8}</level> | "
                "<cyan>{name}</cyan>:<green>{function}</green>:<yellow>{line}</yellow> - "
                "<level>{message}</level>"
            ),
            level=self.logging_level,
        )
