import datetime as dt
import logging
from typing import Any

import pandas as pd

from app.models.advisor import AdvisorMessage

logger = logging.getLogger(__name__)

_LOW_CONFIDENCE_MSG = (
    "ขออภัยค่ะ ระบบไม่เข้าใจความต้องการของท่าน โปรดอธิบายความต้องการของท่านให้ชัดเจนขึ้น"
)


class AdvisorReply:
    def __init__(self, data: dict[str, Any]) -> None:
        self.input_data = data
        self.customer_info: dict[str, Any] = data.get("user_info", {})
        conv_desc: dict[str, Any] = data.get("conversation_desc", {})
        self.conversation_data: dict[str, Any] = {
            "session_id": data.get("session_id"),
            "customer_id": data.get("customer_id"),
            "user_message": data.get("user_message"),
            "conversation_desc": conv_desc,
            "narrative": conv_desc.get("narrative", ""),
            "tone_guidance": conv_desc.get("tone_guidance", ""),
            "history": data.get("history", []),
            "timestamp": data.get("timestamp"),
        }
        self.df_acc = pd.DataFrame([item["json"] for item in data.get("acc_info", [])])
        self.agent_result: dict[str, Any] = {}

    async def _gen_reply(self) -> None:
        self.agent_result = {}

    async def produce_reply(self) -> dict[str, Any]:
        try:
            await self._gen_reply()
            agent_output = AdvisorMessage(**self.agent_result).model_dump()
            if agent_output["confidence"] <= 0.3:
                agent_output["reply_message"] = _LOW_CONFIDENCE_MSG
        except Exception:
            logger.exception("Agent reply generation failed; returning system error default")
            agent_output = AdvisorMessage().model_dump()

        return {
            "session_id": self.input_data.get("session_id"),
            "customer_id": self.input_data.get("customer_id"),
            "user_message": self.input_data.get("user_message"),
            "agent_output": agent_output,
            "timestamp": dt.datetime.now().isoformat(timespec="milliseconds"),
        }
