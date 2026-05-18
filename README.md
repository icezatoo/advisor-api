# DebtMind Advisor API

AI-powered debt advisory API built with FastAPI. Designed for use with n8n workflows and LLM providers (OpenAI, Google).

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — install once with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Setup

```bash
# 1. Install dependencies
make install

# 2. Copy env file and add your API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

---

## Running the server

```bash
make dev
```

Server starts at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

---

## Running tests

```bash
make test
```

---

## Lint / format

```bash
make lint     # check for issues
make format   # auto-fix formatting
```

---

## API Endpoints

### `GET /health`

Check that the server is running.

```bash
curl http://localhost:8000/health
```

Response:

```json
{"status": "ok"}
```

---

### `POST /advisor/query`

Ask the AI debt advisor a question on behalf of a customer.

**Request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `session_id` | string | yes | Chat/conversation identifier |
| `customer.name` | string | yes | Customer's full name |
| `customer.monthly_income` | number | yes | Monthly income in USD |
| `customer.debts` | array | no | List of debt objects |
| `customer.debts[].name` | string | yes | Debt label (e.g. "credit_card") |
| `customer.debts[].balance` | number | yes | Remaining balance in USD |
| `customer.debts[].interest_rate` | number | yes | Annual rate as decimal (0.22 = 22%) |
| `message` | string | yes | The customer's question |
| `history` | array | no | Previous chat messages for context |

**Basic query:**

```bash
curl -X POST http://localhost:8000/advisor/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "chat-001",
    "customer": {
      "name": "John Doe",
      "monthly_income": 5000,
      "debts": [
        {"name": "credit_card", "balance": 8000, "interest_rate": 0.22},
        {"name": "car_loan", "balance": 12000, "interest_rate": 0.06}
      ]
    },
    "message": "Which debt should I pay off first?"
  }'
```

**Query with chat history:**

```bash
curl -X POST http://localhost:8000/advisor/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "chat-001",
    "customer": {
      "name": "John Doe",
      "monthly_income": 5000,
      "debts": [
        {"name": "credit_card", "balance": 8000, "interest_rate": 0.22}
      ]
    },
    "message": "How long will it take to pay it off?",
    "history": [
      {"role": "user", "content": "Which debt should I pay off first?"},
      {"role": "assistant", "content": "Pay off the credit card first — its 22% rate costs you the most."}
    ]
  }'
```

Response shape:

```json
{
  "session_id": "chat-001",
  "answer": "Based on your income, pay off the credit card first...",
  "sources": []
}
```

---

## n8n Integration

Use the **HTTP Request** node with:

- **Method**: POST
- **URL**: `http://your-host:8000/advisor/query`
- **Body (JSON)**:

```json
{
  "query": "{{ $json.query }}",
  "context": {{ $json.context }}
}
```

---

## Project Structure

```
advisor-api/
├── app/
│   ├── main.py          # FastAPI app factory + /health
│   ├── config.py        # Environment settings
│   ├── routers/
│   │   └── advisor.py   # POST /advisor/query
│   └── services/
│       └── llm.py       # OpenAI client
├── tests/
│   └── test_advisor.py
├── Makefile
├── pyproject.toml
└── .env.example
```
