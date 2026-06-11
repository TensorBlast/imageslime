#!/bin/bash
# ImageSlime - UV Setup Script
# This script helps set up the project with uv

set -e

echo "🎨 ImageSlime - UV Setup"
echo "========================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "🔍 uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
fi

# Check uv version
uv --version

echo ""
echo "📦 Syncing dependencies..."
uv sync

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run ImageSlime:"
echo "  uv run python main.py"
echo ""
echo "Or to start the server directly:"
echo "  uv run uvicorn imageslime.main:app --reload"
echo ""
echo "Access the app at: http://localhost:8000"
