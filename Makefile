.PHONY: install dev test lint format check-uv

check-uv:
	@which uv > /dev/null 2>&1 || (echo "uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)

install: check-uv
	uv sync --all-groups

dev: check-uv
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: check-uv
	uv run pytest -v

lint: check-uv
	uv run ruff check .

format: check-uv
	uv run ruff format .
