from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_query_advisor_success(client):
    with patch("app.services.llm.complete", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Your debt-to-income ratio looks healthy."
        response = await client.post(
            "/advisor/query",
            json={"query": "What is my debt-to-income ratio?"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Your debt-to-income ratio looks healthy."
    assert "sources" in data


async def test_query_advisor_with_context(client):
    with patch("app.services.llm.complete", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Based on your income, pay off the high-interest debt first."
        response = await client.post(
            "/advisor/query",
            json={
                "query": "Which debt should I pay off first?",
                "context": {"monthly_income": 5000, "total_debt": 20000},
            },
        )
    assert response.status_code == 200
    assert response.json()["answer"] != ""


async def test_query_advisor_no_llm_key(client):
    from fastapi import HTTPException

    with patch(
        "app.services.llm.complete",
        side_effect=HTTPException(
            status_code=503, detail="LLM service unavailable: OPENAI_API_KEY is not configured"
        ),
    ):
        response = await client.post(
            "/advisor/query",
            json={"query": "Test query"},
        )
    assert response.status_code == 503
