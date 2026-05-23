import json
from collections import defaultdict, deque
from typing import Deque

from loguru import logger
from redis.asyncio import Redis


class ChatCleanupRepository:
    def __init__(self, redis_client: Redis | None = None, limit: int = 100) -> None:
        self.redis_client = redis_client
        self.limit = limit
        self._fallback_storage: dict[int, Deque[int]] = defaultdict(lambda: deque(maxlen=self.limit))

    def _redis_key(self, chat_id: int) -> str:
        return f"chat_cleanup:{chat_id}"

    async def add_message_id(self, chat_id: int, message_id: int) -> None:
        if self.redis_client is None:
            self._fallback_storage[chat_id].appendleft(message_id)
            return

        try:
            await self.redis_client.lpush(self._redis_key(chat_id), json.dumps(message_id))
            await self.redis_client.ltrim(self._redis_key(chat_id), 0, self.limit - 1)
        except Exception:
            logger.exception("Failed to store message id for chat cleanup")
            self._fallback_storage[chat_id].appendleft(message_id)

    async def get_message_ids(self, chat_id: int) -> list[int]:
        if self.redis_client is None:
            return list(self._fallback_storage[chat_id])

        try:
            items = await self.redis_client.lrange(self._redis_key(chat_id), 0, self.limit - 1)
            return [int(json.loads(item)) for item in items]
        except Exception:
            logger.exception("Failed to read message ids for chat cleanup")
            return list(self._fallback_storage[chat_id])

    async def clear_message_ids(self, chat_id: int) -> None:
        if self.redis_client is None:
            self._fallback_storage.pop(chat_id, None)
            return

        try:
            await self.redis_client.delete(self._redis_key(chat_id))
        except Exception:
            logger.exception("Failed to clear message ids for chat cleanup")
            self._fallback_storage.pop(chat_id, None)
