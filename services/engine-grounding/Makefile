.PHONY: install test lint format run clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

run:
	uvicorn engine_grounding.main:create_app --factory --host 0.0.0.0 --port 8002 --reload

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
