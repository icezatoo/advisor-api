import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

_SYSTEM_PROMPT = """\
คุณเป็น AI ที่ปรึกษาด้านหนี้สินของธนาคาร ช่วยให้คำแนะนำลูกค้าเกี่ยวกับการจัดการหนี้

ข้อมูลลูกค้า:
{customer_info}

ข้อมูลบัญชี:
{acc_info}

บริบทการสนทนา:
- narrative: {narrative}
- tone_guidance: {tone_guidance}

กฎ:
- ตอบเป็นภาษาไทยเสมอ
- ให้คำแนะนำที่ตรงประเด็นและเหมาะสมกับ tone_guidance
- ตอบใน JSON format เท่านั้น ตามโครงสร้างนี้:
{{
  "reply_message": "ข้อความตอบกลับลูกค้า",
  "consider_account": "หมายเลขบัญชีที่เกี่ยวข้อง หรือ '' ถ้าไม่มี",
  "confidence": 0.0,
  "reason": "เหตุผลในการแนะนำ",
  "narrative": "สรุปสถานการณ์ลูกค้า"
}}
- confidence คือระดับความมั่นใจ 0.0–1.0
"""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = settings.litellm_api_key or settings.google_api_key
        if not api_key:
            raise ValueError("LITELLM_API_KEY or GOOGLE_API_KEY must be set")
        _client = AsyncOpenAI(
            base_url=f"{settings.litellm_api_base.rstrip('/')}/v1",
            api_key=api_key,
        )
    return _client


async def complete(
    conversation_data: dict[str, Any],
    customer_info: dict[str, Any],
    acc_summary: str,
) -> dict[str, Any]:
    customer_str = "\n".join(f"  {k}: {v}" for k, v in customer_info.items()) or "ไม่มีข้อมูล"

    system_prompt = _SYSTEM_PROMPT.format(
        customer_info=customer_str,
        acc_info=acc_summary or "ไม่มีข้อมูลบัญชี",
        narrative=conversation_data.get("narrative", ""),
        tone_guidance=conversation_data.get("tone_guidance", ""),
    )

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in conversation_data.get("history", []):
        is_bot = msg.get("role", "").upper() in ("BOT", "ASSISTANT", "MODEL")
        role = "assistant" if is_bot else "user"
        messages.append({"role": role, "content": msg.get("content", "")})
    messages.append({"role": "user", "content": conversation_data.get("user_message", "")})

    logger.debug(
        "Calling LiteLLM session=%s customer=%s",
        conversation_data.get("session_id"),
        conversation_data.get("customer_id"),
    )

    response = await _get_client().chat.completions.create(
        model=settings.litellm_model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    content = response.choices[0].message.content if response.choices else None
    return json.loads(content or "{}")
