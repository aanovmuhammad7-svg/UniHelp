from typing import Callable, Coroutine, Any
from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from app.database.db_events import connect_to_database, close_database_connection
from app.database.redis_events import connect_to_redis, close_redis_connection


def create_start_app_handler(app: FastAPI, settings: AppSettings) -> Callable[[], Coroutine[Any, Any, None]]:
    @logger.catch
    async def start_app() -> None:
        await connect_to_database(app, settings)
        await connect_to_redis(app)
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable[[], Coroutine[Any, Any, None]]:
    @logger.catch
    async def stop_app() -> None:
        await close_database_connection(app)
        await close_redis_connection(app)
    return stop_app