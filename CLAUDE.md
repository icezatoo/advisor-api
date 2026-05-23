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

Single-endpoint FastAPI service. Current request flow:

```
POST /advisor/query
  → app/routers/advisor.py        — validates AdvisorQueryRequest, instantiates AdvisorReply
  → app/services/advisor_reply.py — AdvisorReply.produce_reply() calls _gen_reply()
```

**AdvisorReply is the primary extension point.** `_gen_reply()` calls `app/services/gemini.py` which sends the request to a LiteLLM proxy (`LITELLM_API_BASE`) using the OpenAI-compatible API. To swap in a different agent, subclass `AdvisorReply` and override `_gen_reply()` to populate `self.agent_result` with fields matching `AdvisorMessage`.

**`AdvisorMessage` confidence gate:** `produce_reply()` checks `agent_output["confidence"] <= 0.3` after `_gen_reply()` completes; if true, it overrides `reply_message` with a canned Thai low-confidence fallback. The exception path returns the `AdvisorMessage()` default (Thai error string) without going through the gate.

**`acc_info` parsing:** `AdvisorReply.__init__` unpacks `acc_info[*].json` into `self.df_acc` (a pandas DataFrame), making per-account data available as structured tabular data to `_gen_reply()`.

**`app/services/llm.py`** is a legacy OpenAI wrapper (`gpt-4o-mini`, stateless, builds a system prompt from a `Customer` object). It is **not yet wired** into `AdvisorReply` — it exists for the old single-endpoint design and will need adaptation when real LLM calls are added.

**Key design decisions:**

- No server-side session state. Multi-turn context arrives as `history` in each request; `conversation_desc` carries narrative and tone metadata set by the caller (n8n).
- `app/config.py` uses `pydantic-settings` — all config sourced from `.env` or environment variables. `ALLOWED_ORIGINS` is comma-separated, parsed by the `origins_list` property.
- Tests subclass `AdvisorReply` and override `_gen_reply()` directly to inject known `agent_result` values — no mocking framework needed.

## Environment

Copy `.env.example` to `.env`. `OPENAI_API_KEY` is required only when `llm.py` is wired up. `GOOGLE_API_KEY` is in config but unused. `ALLOWED_ORIGINS` controls CORS and defaults to n8n (`:5678`) and a local frontend (`:3000`).
