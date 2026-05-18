import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import llm

logger = logging.getLogger(__name__)

router = APIRouter()


class AdvisorRequest(BaseModel):
    query: str
    context: dict | None = None


class AdvisorResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/query", response_model=AdvisorResponse)
async def query_advisor(request: AdvisorRequest) -> AdvisorResponse:
    logger.info("Received advisor query: %s", request.query[:80])
    try:
        answer = await llm.complete(request.query, request.context)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error processing query")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    return AdvisorResponse(answer=answer)
