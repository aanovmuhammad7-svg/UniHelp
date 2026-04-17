from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

def create_redis() -> Redis:
    pool = ConnectionPool.from_url(# type: ignore
        settings.redis_url.unicode_string(),
        decode_responses=True,
        max_connections=settings.redis_max_connections
    )
    return Redis(connection_pool=pool)

redis_client: Redis = create_redis()