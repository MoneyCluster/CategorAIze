#!/bin/bash
# Локальный запуск документации (сборка LikeC4 + mkdocs serve)
set -euo pipefail

ADDR=${ADDR:-127.0.0.1:8000}

# Ensure we're in repo root (where mkdocs.yml is)
if [ ! -f "mkdocs.yml" ]; then
  echo "❌ mkdocs.yml not found. Run from repo root or 'cd' to project root."
  exit 1
fi

# Build LikeC4 (optional)
if [ "${SKIP_LIKEC4:-0}" != "1" ]; then
  if command -v npx >/dev/null 2>&1; then
    echo "🔨 Building LikeC4 diagrams... (set SKIP_LIKEC4=1 to skip)"
    ./scripts/build-likec4.sh || echo "⚠️ LikeC4 build failed — continuing with existing static assets"
  else
    echo "ℹ️ Node.js/npx not found. Skipping LikeC4 build. Set SKIP_LIKEC4=1 to silence."
  fi
fi

# Start a local SPA server for LikeC4 to support history routing
if command -v npx >/dev/null 2>&1; then
  echo "🛰  Starting LikeC4 SPA server on http://127.0.0.1:5173 (history fallback)"
  npx --yes serve@14 -s docs/_static/likec4 -l 5173 >/dev/null 2>&1 &
  LIKEC4_SPA_PID=$!
fi

# Ensure MkDocs is available
if ! command -v mkdocs >/dev/null 2>&1; then
  echo "ℹ️ 'mkdocs' CLI not found; trying 'python3 -m mkdocs'"
  if ! python3 -c "import mkdocs" >/dev/null 2>&1; then
    echo "📦 Installing MkDocs and plugins (mkdocs-material, macros, include-markdown)"
    python3 -m pip install --upgrade pip >/dev/null
    python3 -m pip install mkdocs-material mkdocs-macros-plugin mkdocs-include-markdown-plugin >/dev/null
  fi
fi

echo "🚀 Starting MkDocs on http://${ADDR}/"
# Set PYTHONPATH so docs._macros.main can be imported
export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
if command -v mkdocs >/dev/null 2>&1; then
  mkdocs serve --dev-addr="${ADDR}"
else
  python3 -m mkdocs serve --dev-addr="${ADDR}"
fi
