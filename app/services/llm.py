import logging

from fastapi import HTTPException
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def complete(query: str, context: dict | None = None) -> str:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable: OPENAI_API_KEY is not configured",
        )

    system_prompt = "You are a helpful debt advisor. Provide clear, accurate financial guidance."
    user_message = query
    if context:
        user_message = f"Context: {context}\n\nQuery: {query}"

    client = _get_client()
    logger.debug("Calling OpenAI with query length %d", len(query))
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
