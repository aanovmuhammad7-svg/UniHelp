import json
from collections import defaultdict, deque
from typing import Deque

from loguru import logger
from redis.asyncio import Redis

from app.core.config import settings


class ChatHistoryRepository:
    def __init__(self, redis_client: Redis | None = None, history_limit: int | None = None) -> None:
        self.redis_client = redis_client
        self.history_limit = history_limit or settings.chat_history_limit
        self._fallback_storage: dict[int, Deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=self.history_limit)
        )

    def _redis_key(self, user_id: int) -> str:
        return f"chat_history:{user_id}"

    async def get_history(self, user_id: int) -> list[dict[str, str]]:
        if self.redis_client is None:
            return list(self._fallback_storage[user_id])

        try:
            items = await self.redis_client.lrange(self._redis_key(user_id), 0, self.history_limit - 1)
            return [json.loads(item) for item in items]
        except Exception:
            logger.exception("Redis is unavailable, falling back to in-memory chat history")
            return list(self._fallback_storage[user_id])

    async def append_messages(self, user_id: int, messages: list[dict[str, str]]) -> None:
        if not messages:
            return

        if self.redis_client is None:
            storage = self._fallback_storage[user_id]
            for message in messages:
                storage.appendleft(message)
            return

        try:
            key = self._redis_key(user_id)
            payload = [json.dumps(message, ensure_ascii=False) for message in messages]
            await self.redis_client.lpush(key, *payload)
            await self.redis_client.ltrim(key, 0, self.history_limit - 1)
            return
        except Exception:
            logger.exception("Redis is unavailable, storing chat history in memory")

        storage = self._fallback_storage[user_id]
        for message in messages:
            storage.appendleft(message)

    async def clear_history(self, user_id: int) -> None:
        if self.redis_client is None:
            self._fallback_storage.pop(user_id, None)
            return

        try:
            await self.redis_client.delete(self._redis_key(user_id))
        except Exception:
            logger.exception("Redis is unavailable, clearing in-memory chat history")
            self._fallback_storage.pop(user_id, None)
