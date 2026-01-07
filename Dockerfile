# Dockerfile для офлайн-инференса модели
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Настройка Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Рабочая директория
WORKDIR /app

# Копирование файлов зависимостей
COPY pyproject.toml poetry.lock ./

# Установка зависимостей
RUN poetry install --no-dev && rm -rf $POETRY_CACHE_DIR

# Копирование исходного кода
COPY src/ /app/src/

# Установка DVC для загрузки модели (если нужно)
RUN poetry run pip install dvc

# Копирование DVC конфигурации (если есть)
COPY .dvc/ .dvc/
COPY dvc.yaml dvc.lock .dvcignore ./

# Загрузка модели через DVC (опционально, можно также скопировать напрямую)
# RUN poetry run dvc pull || echo "DVC pull failed, model should be copied directly"

# Установка переменных окружения
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

# Entrypoint
ENTRYPOINT ["python", "-m", "categoraize.predict"]

