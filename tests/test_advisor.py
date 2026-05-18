from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

CUSTOMER = {
    "name": "John Doe",
    "monthly_income": 5000,
    "debts": [
        {"name": "credit_card", "balance": 8000, "interest_rate": 0.22},
        {"name": "car_loan", "balance": 12000, "interest_rate": 0.06},
    ],
}


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
        mock_llm.return_value = "Pay off the credit card first due to its high interest rate."
        response = await client.post(
            "/advisor/query",
            json={
                "session_id": "test-session-001",
                "customer": CUSTOMER,
                "message": "Which debt should I pay off first?",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-001"
    assert data["answer"] == "Pay off the credit card first due to its high interest rate."
    assert "sources" in data


async def test_query_advisor_with_history(client):
    with patch("app.services.llm.complete", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Your debt-to-income ratio is 0.64, which is high."
        response = await client.post(
            "/advisor/query",
            json={
                "session_id": "test-session-002",
                "customer": CUSTOMER,
                "message": "What is my debt-to-income ratio?",
                "history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help?"},
                ],
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
            json={
                "session_id": "test-session-003",
                "customer": CUSTOMER,
                "message": "Test query",
            },
        )
    assert response.status_code == 503
