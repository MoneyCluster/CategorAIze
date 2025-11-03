#!/bin/bash
# Скрипт для локальной сборки LikeC4 диаграмм
set -euo pipefail

if ! command -v npx >/dev/null 2>&1; then
  echo "❌ npx not found. Install Node.js (>=20) to build LikeC4."
  exit 1
fi

echo "🔨 Building LikeC4 diagrams (with base=/CategorAIze/_static/likec4)..."
npx --yes likec4@latest build --config docs/_likec4/likec4.config.ts --base "/CategorAIze/_static/likec4" --output dist-likec4

echo "📦 Copying artifacts to docs/_static/likec4..."
rm -rf docs/_static/likec4
mkdir -p docs/_static/likec4
cp -R dist-likec4/* docs/_static/likec4/

echo "🧹 Cleaning up..."
rm -rf dist-likec4

echo "✅ Done! LikeC4 diagrams are ready in docs/_static/likec4/"

