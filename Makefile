# ImageSlime Makefile
# Use uv for fast dependency management

.PHONY: help install sync run dev test lint format clean

# Default target
help:
	@echo "ImageSlime - Makefile Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install uv and sync dependencies"
	@echo "  make sync       - Sync dependencies with uv"
	@echo ""
	@echo "Running:"
	@echo "  make run        - Run the server"
	@echo "  make dev        - Run with auto-reload for development"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run basic tests"
	@echo "  make pytest     - Run pytest"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Format code with black"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean      - Remove build artifacts and cache"
	@echo ""

# Install uv and sync dependencies
install:
	@echo "🔧 Installing uv..."
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "📦 Syncing dependencies..."
	uv sync
	@echo "✅ Setup complete!"

# Sync dependencies
sync:
	uv sync

# Run the server
run:
	uv run python main.py

# Run with auto-reload for development
dev:
	uv run uvicorn imageslime.main:app --reload

# Run basic tests
test:
	uv run python test_basic.py

# Run pytest
pytest:
	uv run pytest

# Run linter
lint:
	uv run ruff check imageslime/

# Format code
format:
	uv run black imageslime/
	uv run black main.py
	uv run black test_basic.py
	uv run black setup.py

# Clean build artifacts
clean:
	rm -rf .venv/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/
	rm -rf uv.lock
	@echo "🧹 Cleaned up!"

# Run setup script
setup:
	uv run python setup.py

# Check SAM3 model status
check-model:
	uv run python -c "from imageslime.services.segmentation import get_segmentation_service; print(get_segmentation_service().get_model_info())"

# Export requirements.txt
export-reqs:
	uv export -f requirements.txt --no-dev

# Export full requirements.txt (with dev)
export-reqs-dev:
	uv export -f requirements-dev.txt --all-extras
