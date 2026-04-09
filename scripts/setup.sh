#!/bin/bash
set -e

echo "=== ZROKY Development Setup ==="
echo ""

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "Error: Node.js required (v20+)"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "Error: pnpm required (v9+)"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: Python 3.11+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Error: Docker required"; exit 1; }

echo "1. Installing Node.js dependencies..."
pnpm install

echo ""
echo "2. Setting up Python virtual environments..."
for dir in services/engine-* services/trust-computer services/health-check; do
  echo "   → $dir"
  (cd "$dir" && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" -q)
done

echo ""
echo "3. Copying environment files..."
if [ ! -f .env ]; then
  cp .env.example .env 2>/dev/null || echo "   (No .env.example yet — skip)"
fi

echo ""
echo "4. Starting local databases..."
docker compose up -d

echo ""
echo "5. Setting up git hooks..."
npx husky

echo ""
echo "=== Setup complete! ==="
echo "Run 'pnpm dev' to start all services."
