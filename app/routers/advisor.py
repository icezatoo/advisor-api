import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.models.advisor import AdvisorMessage
from app.services.advisor_reply import AdvisorReply

logger = logging.getLogger(__name__)

router = APIRouter()


class AccInfoItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    data: dict[str, Any] = Field(alias="json")


class ConversationDesc(BaseModel):
    consult_acc: str = ""
    narrative: str = ""
    tone_guidance: str = ""


class HistoryMessage(BaseModel):
    role: str
    content: str


class AdvisorQueryRequest(BaseModel):
    session_id: str
    customer_id: str
    user_message: str
    user_info: dict[str, Any] = {}
    acc_info: list[AccInfoItem] = []
    history: list[HistoryMessage] = []
    conversation_desc: ConversationDesc = ConversationDesc()
    timestamp: str = ""


class AdvisorQueryResponse(BaseModel):
    session_id: str
    customer_id: str
    user_message: str
    agent_output: AdvisorMessage
    timestamp: str


@router.post("/query", response_model=AdvisorQueryResponse)
async def query_advisor(request: AdvisorQueryRequest) -> AdvisorQueryResponse:
    logger.info(
        "session=%s customer=%s message=%s",
        request.session_id,
        request.customer_id,
        request.user_message[:80],
    )
    reply = AdvisorReply(request.model_dump(by_alias=True))
    result = await reply.produce_reply()
    return AdvisorQueryResponse(**result)
