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

Ask the AI debt advisor a question.

**Basic query:**

```bash
curl -X POST http://localhost:8000/advisor/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a good debt-to-income ratio?"}'
```

**Query with financial context:**

```bash
curl -X POST http://localhost:8000/advisor/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which debt should I pay off first?",
    "context": {
      "monthly_income": 5000,
      "debts": [
        {"name": "credit_card", "balance": 8000, "interest_rate": 0.22},
        {"name": "car_loan", "balance": 12000, "interest_rate": 0.06}
      ]
    }
  }'
```

Response shape:

```json
{
  "answer": "Based on your situation, pay off the credit card first...",
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
