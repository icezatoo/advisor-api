from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.advisor_reply import _LOW_CONFIDENCE_MSG, AdvisorReply

PAYLOAD: dict[str, Any] = {
    "session_id": "test-001",
    "customer_id": "1210003",
    "user_message": "ต้องการลดภาระการผ่อน",
    "user_info": {
        "CustomerSegment": "C1",
        "EligibleProgram": "KhunSuu, PL_MOU",
        "IncomeFromSystem": 47000,
    },
    "acc_info": [
        {
            "json": {
                "accNo": "10000004",
                "os": 320000,
                "intRate": 0.06,
                "installment": 7500,
                "remainTerm": 48,
                "currentDPD": 12,
            }
        }
    ],
    "history": [{"role": "BOT", "content": "สวัสดีค่ะ"}],
    "conversation_desc": {
        "consult_acc": "",
        "narrative": "ลูกค้าต้องการลดภาระ",
        "tone_guidance": "very_empathetic",
    },
    "timestamp": "2026-05-18T02:27:13.575Z",
}


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_query_response_shape(client):
    response = await client.post("/advisor/query", json=PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == PAYLOAD["session_id"]
    assert data["customer_id"] == PAYLOAD["customer_id"]
    assert data["user_message"] == PAYLOAD["user_message"]
    assert "timestamp" in data
    assert set(data["agent_output"].keys()) == {
        "reply_message",
        "consider_account",
        "confidence",
        "reason",
        "narrative",
    }


async def test_stub_applies_low_confidence_gate(client):
    # gemini.complete returns {} → confidence=0 → gate overrides reply_message
    with patch("app.services.gemini.complete", new=AsyncMock(return_value={})):
        response = await client.post("/advisor/query", json=PAYLOAD)
    data = response.json()
    assert data["agent_output"]["confidence"] == 0
    assert data["agent_output"]["reply_message"] == _LOW_CONFIDENCE_MSG


async def test_produce_reply_high_confidence():
    class HighConfidenceReply(AdvisorReply):
        async def _gen_reply(self) -> None:
            self.agent_result = {
                "reply_message": "แนะนำโปรแกรม PL_MOU ค่ะ",
                "consider_account": "10000004",
                "confidence": 0.9,
                "reason": "C1 segment, eligible for PL_MOU",
                "narrative": "ลูกค้าต้องการลดภาระ",
            }

    result = await HighConfidenceReply(PAYLOAD).produce_reply()
    out = result["agent_output"]
    assert out["confidence"] == 0.9
    assert out["reply_message"] == "แนะนำโปรแกรม PL_MOU ค่ะ"


async def test_produce_reply_exception_returns_system_error():
    class FailingReply(AdvisorReply):
        async def _gen_reply(self) -> None:
            raise RuntimeError("LLM unavailable")

    result = await FailingReply(PAYLOAD).produce_reply()
    out = result["agent_output"]
    # Exception path returns AdvisorMessage() defaults without confidence gate
    assert out["reply_message"] == "ระบบประมวลผลขัดข้อง กรุณาถามคำถามใหม่อีกครั้ง"
    assert out["confidence"] == 0


async def test_df_acc_parsed_from_acc_info():
    reply = AdvisorReply(PAYLOAD)
    assert len(reply.df_acc) == 1
    assert reply.df_acc.iloc[0]["accNo"] == "10000004"


async def test_conversation_desc_extracted():
    reply = AdvisorReply(PAYLOAD)
    assert reply.conversation_data["narrative"] == "ลูกค้าต้องการลดภาระ"
    assert reply.conversation_data["tone_guidance"] == "very_empathetic"
