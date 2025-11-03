#!/bin/bash
# Локальный запуск документации (сборка LikeC4 + mkdocs serve)
# Использование: ./scripts/serve-docs.sh [--skip-likec4] [--port PORT]
set -euo pipefail

ADDR=${ADDR:-127.0.0.1:8000}
SKIP_LIKEC4=0

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-likec4)
      SKIP_LIKEC4=1
      shift
      ;;
    --port)
      ADDR="127.0.0.1:${2:-8000}"
      shift 2
      ;;
    --help|-h)
      echo "Запуск локального сервера документации"
      echo ""
      echo "Использование: ./scripts/serve-docs.sh [опции]"
      echo ""
      echo "Опции:"
      echo "  --skip-likec4     Пропустить сборку LikeC4 диаграмм"
      echo "  --port PORT       Запустить на указанном порту (по умолчанию: 8000)"
      echo "  --help, -h        Показать эту справку"
      echo ""
      echo "Примеры:"
      echo "  ./scripts/serve-docs.sh"
      echo "  ./scripts/serve-docs.sh --skip-likec4"
      echo "  ./scripts/serve-docs.sh --port 9000"
      exit 0
      ;;
    *)
      echo "❌ Неизвестный аргумент: $1"
      echo "Использование: ./scripts/serve-docs.sh [--skip-likec4] [--port PORT]"
      echo "Для справки: ./scripts/serve-docs.sh --help"
      exit 1
      ;;
  esac
done

# Ensure we're in repo root (where mkdocs.yml is)
if [ ! -f "mkdocs.yml" ]; then
  echo "❌ mkdocs.yml not found. Run from repo root or 'cd' to project root."
  exit 1
fi

# Build LikeC4 (optional)
if [ "${SKIP_LIKEC4}" != "1" ]; then
  if command -v npx >/dev/null 2>&1; then
    echo "🔨 Building LikeC4 diagrams... (set SKIP_LIKEC4=1 to skip)"
    ./scripts/build-likec4.sh || echo "⚠️ LikeC4 build failed — continuing with existing static assets"
  else
    echo "ℹ️ Node.js/npx not found. Skipping LikeC4 build. Set SKIP_LIKEC4=1 to silence."
  fi
fi

## No separate SPA server: use MkDocs-served static assets

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
