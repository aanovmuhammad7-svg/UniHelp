from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text

from app.core.settings.app import AppSettings
from app.database.database import engine


async def connect_to_database(app: FastAPI, settings: AppSettings) -> None:
    logger.info("Connecting to PostgreSQL...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as exc:
        logger.exception(f"Error connecting to database: {exc}")
        raise


async def close_database_connection(app: FastAPI) -> None:
    logger.info("Closing database connection...")
    try:
        await engine.dispose()
        logger.info("Database connection closed")
    except Exception as exc:
        logger.exception(f"Error closing database connection: {exc}")
