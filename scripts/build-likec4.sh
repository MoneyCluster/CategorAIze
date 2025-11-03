#!/bin/bash
# Скрипт для локальной сборки LikeC4 диаграмм
set -euo pipefail

if ! command -v npx >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js/npx not found. Install Node.js (>=20) to build LikeC4."
  exit 1
fi

# Remove site/_likec4 if exists to prevent LikeC4 from finding duplicate project
if [ -d "site/_likec4" ]; then
  echo "🧹 Removing site/_likec4 to avoid duplicate projects..."
  rm -rf site/_likec4
fi

echo "🔨 Building LikeC4 diagrams (with base=/CategorAIze/_static/likec4, hash-history)..."
npx --yes likec4@latest build --config docs/_likec4/likec4.config.ts --base "/CategorAIze/_static/likec4" --use-hash-history --output dist-likec4

echo "📦 Copying artifacts to docs/_static/likec4..."
rm -rf docs/_static/likec4
mkdir -p docs/_static/likec4
cp -R dist-likec4/* docs/_static/likec4/

echo "🧹 Cleaning up..."
rm -rf dist-likec4

echo "✅ Done! LikeC4 diagrams are ready in docs/_static/likec4/"

