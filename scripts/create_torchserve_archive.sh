#!/bin/bash
# Скрипт для создания TorchServe архива модели

set -e

MODEL_NAME=${1:-mymodel}
MODEL_VERSION=${2:-1.0}
MODEL_PATH=${3:-models/checkpoint}
HANDLER_PATH=${4:-torchserve/handler.py}
EXPORT_PATH=${5:-model-store}

echo "Создание TorchServe архива модели..."
echo "  Model name: $MODEL_NAME"
echo "  Version: $MODEL_VERSION"
echo "  Model path: $MODEL_PATH"
echo "  Handler: $HANDLER_PATH"
echo "  Export path: $EXPORT_PATH"

# Проверка наличия torch-model-archiver
if ! command -v torch-model-archiver &> /dev/null; then
    echo "torch-model-archiver не найден. Установка..."
    pip install torchserve torch-model-archiver
fi

# Создание директории для архива
mkdir -p "$EXPORT_PATH"

# Создание архива
torch-model-archiver \
    --model-name "$MODEL_NAME" \
    --version "$MODEL_VERSION" \
    --handler "$HANDLER_PATH" \
    --extra-files "$MODEL_PATH" \
    --export-path "$EXPORT_PATH" \
    --force

echo "Архив создан: $EXPORT_PATH/$MODEL_NAME.mar"

