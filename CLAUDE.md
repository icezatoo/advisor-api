# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands require [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
make install      # install all dependencies (including dev)
make dev          # run dev server with hot reload on :8000
make test         # run all tests
make lint         # ruff check
make format       # ruff format (auto-fix)
```

Run a single test file or test function:
```bash
uv run pytest tests/test_advisor.py::test_health -v
```

## Architecture

This is a single-endpoint FastAPI service. The request flow is:

```
POST /advisor/query
  → app/routers/advisor.py   — validates AdvisorRequest, calls llm.complete()
  → app/services/llm.py      — builds system prompt from customer profile, calls OpenAI
```

**Key design decisions:**

- `app/services/llm.py` constructs a fresh system prompt per request by injecting the full customer profile (name, income, debts) into the `system` message. No state is stored server-side; multi-turn context is passed in the `history` field by the caller.
- The OpenAI client (`AsyncOpenAI`) is a lazy singleton (`_client`) initialized on first use, keyed to `settings.openai_api_key`.
- `app/config.py` uses `pydantic-settings` — all config is sourced from `.env` or environment variables. `ALLOWED_ORIGINS` is a comma-separated string, parsed into a list by the `origins_list` property.
- Tests use `httpx.ASGITransport` for in-process requests and mock `app.services.llm.complete` directly — no real LLM calls in tests.

## Environment

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. `GOOGLE_API_KEY` is available in config but not yet wired to any service. `ALLOWED_ORIGINS` controls CORS and defaults to n8n (`:5678`) and a local frontend (`:3000`).
