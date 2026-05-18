import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException
from openai import AsyncOpenAI

from app.config import settings

if TYPE_CHECKING:
    from app.routers.advisor import ChatMessage, Customer

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _build_system_prompt(customer: "Customer") -> str:
    debt_lines = "\n".join(
        f"  - {d.name}: balance ${d.balance:,.2f}, interest rate {d.interest_rate * 100:.1f}%"
        for d in customer.debts
    )
    return (
        "You are a helpful debt advisor. Provide clear, accurate financial guidance.\n\n"
        f"Customer profile:\n"
        f"  Name: {customer.name}\n"
        f"  Monthly income: ${customer.monthly_income:,.2f}\n"
        f"  Debts:\n{debt_lines if debt_lines else '  - None listed'}"
    )


async def complete(
    customer: "Customer",
    message: str,
    history: "list[ChatMessage]",
) -> str:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable: OPENAI_API_KEY is not configured",
        )

    messages: list[dict] = [{"role": "system", "content": _build_system_prompt(customer)}]
    messages.extend({"role": msg.role, "content": msg.content} for msg in history)
    messages.append({"role": "user", "content": message})

    client = _get_client()
    logger.debug("Calling OpenAI for customer=%s history_len=%d", customer.name, len(history))
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
