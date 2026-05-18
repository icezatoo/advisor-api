import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter()


class Debt(BaseModel):
    name: str
    balance: float
    interest_rate: float
    type: str | None = None


class Customer(BaseModel):
    name: str
    monthly_income: float
    debts: list[Debt] = []


class ChatMessage(BaseModel):
    role: str
    content: str


class AdvisorRequest(BaseModel):
    session_id: str
    customer: Customer
    message: str
    history: list[ChatMessage] = []


class AdvisorResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str] = []


@router.post("/query", response_model=AdvisorResponse)
async def query_advisor(request: AdvisorRequest) -> AdvisorResponse:
    logger.info(
        "session=%s customer=%s message=%s",
        request.session_id,
        request.customer.name,
        request.message[:80],
    )
    try:
        answer = await llm.complete(request.customer, request.message, request.history)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error processing query")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    return AdvisorResponse(session_id=request.session_id, answer=answer)
