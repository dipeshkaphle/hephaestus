.PHONY: help clean lint test install sync

help:
	@echo "Hephaestus - Makefile commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies with uv"
	@echo "  make sync       - Sync dependencies and create lockfile"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make lint       - Run linting (pytest with pylint & flake8)"
	@echo "  make test       - Run tests"
	@echo ""

install:
	uv sync

sync:
	uv sync --all-extras

clean:
	rm -rf ./build ./dist ./*.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

lint:
	uv run pytest --pylint --flake8 src/

test:
	uv run pytest tests/
