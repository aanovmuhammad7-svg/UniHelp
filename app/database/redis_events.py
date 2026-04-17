from fastapi import FastAPI
from loguru import logger

from app.database.redis import redis_client


async def connect_to_redis(app: FastAPI):
    logger.info("Connecting to Redis...")
    try:
        await redis_client.ping()  # type: ignore
        app.state.redis = redis_client
        logger.info("Redis connection established")
    except Exception as exc:
        logger.exception(f"Error connecting to Redis: {exc}")
        raise


async def close_redis_connection(app: FastAPI):
    logger.info("Closing Redis connection...")
    redis = getattr(app.state, "redis", None)
    if redis is None:
        return
    try:
        await redis.aclose()
        logger.info("Redis connection closed")
    except Exception as exc:
        logger.exception(f"Error closing Redis connection: {exc}")
