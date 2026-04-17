import asyncio

from openai import APITimeoutError, APIConnectionError, AsyncOpenAI, RateLimitError

from app.core.config import settings
from app.repositories.chat_history import ChatHistoryRepository
from app.repositories.user_activity import TelegramProfile, UserActivityRepository
from app.services.knowledge_base import KnowledgeBaseService


class ChatAssistantService:
    def __init__(
        self,
        history_repository: ChatHistoryRepository,
        knowledge_base_service: KnowledgeBaseService,
        user_activity_repository: UserActivityRepository | None = None,
    ) -> None:
        self.history_repository = history_repository
        self.knowledge_base_service = knowledge_base_service
        self.user_activity_repository = user_activity_repository
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        )

    async def answer(
        self,
        user_id: int,
        user_message: str,
        chat_id: int | None = None,
        profile: TelegramProfile | None = None,
    ) -> str:
        history = await self.history_repository.get_history(user_id)
        history = list(reversed(history))
        knowledge_context = self.knowledge_base_service.build_context(user_message)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": settings.assistant_system_prompt},
        ]
        if knowledge_context:
            messages.append({"role": "system", "content": knowledge_context})

        messages.extend(
            [
            *history,
            {"role": "user", "content": user_message},
            ]
        )

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,  # type: ignore[arg-type]
                    max_tokens=settings.openai_max_tokens,
                ),
                timeout=settings.openai_timeout_seconds + 2,
            )
        except (APITimeoutError, asyncio.TimeoutError) as exc:
            raise RuntimeError(
                "OpenAI request timed out. Check network access or reduce request size."
            ) from exc
        except APIConnectionError as exc:
            raise RuntimeError(
                "OpenAI connection failed. Check internet access and API availability."
            ) from exc
        except RateLimitError as exc:
            error_payload = getattr(exc, "body", {}) or {}
            error_info = error_payload.get("error", {}) if isinstance(error_payload, dict) else {}
            error_code = error_info.get("code")
            if error_code == "insufficient_quota":
                raise RuntimeError(
                    "OpenAI API quota is exhausted or billing is not enabled for this key."
                ) from exc
            raise RuntimeError(
                "OpenAI rate limit exceeded. Please try again a bit later."
            ) from exc

        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            answer = "Не удалось сгенерировать ответ. Попробуй сформулировать вопрос немного иначе."

        await self.history_repository.append_messages(
            user_id,
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": answer},
            ],
        )

        if self.user_activity_repository is not None and profile is not None and chat_id is not None:
            db_user_id = await self.user_activity_repository.upsert_user(profile)
            if db_user_id is not None:
                await self.user_activity_repository.save_message(db_user_id, chat_id, "user", user_message)
                await self.user_activity_repository.save_message(db_user_id, chat_id, "assistant", answer)
        return answer

    async def reset_dialog(self, user_id: int) -> None:
        await self.history_repository.clear_history(user_id)
