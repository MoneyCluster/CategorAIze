# CategorAIze

Система персонализированной классификации финансовых трат пользователей с использованием ML.

![Coverage](coverage-badge.svg)

Документация проекта размещена на [GitHub Pages](https://moneycluster.github.io/CategorAIze/).

## Цель проекта

**Бизнес-цель:** Автоматизировать классификацию пользовательских финансовых трат по персонализированным категориям, сократив время на ручную разметку и повысив точность категоризации.

**Проблема:** Каждый пользователь использует свои категории для учета финансов (например, "Продукты", "Транспорт", "Подписки"). Традиционные подходы с единой глобальной моделью не работают из-за индивидуальности категорий.

**Решение:** Персонализированные ML-модели для каждого пользователя:
- Общая модель эмбеддингов (`sentence-transformers`) для преобразования текстовых описаний трат в векторы
- Персональные легкие классификаторы (например, LogisticRegression или MLP) для каждого пользователя
- Обучение на исторических данных пользователя с возможностью улучшения через обратную связь

## Набор данных

Для обучения модели используется публичный датасет **Massive Product Text Classification Dataset** с Kaggle:
- **Источник:** [https://www.kaggle.com/datasets/asaniczka/product-titles-text-classification/data](https://www.kaggle.com/datasets/asaniczka/product-titles-text-classification/data)
- **Структура данных:**
  - Датасет может содержать колонки с разными названиями (например, `title` и `category_name`)
  - Код автоматически определяет нужные колонки или использует маппинг из конфигурации
  - После обработки используются стандартные имена: `product_title` и `category`
- **Характеристики:** Датасет содержит названия продуктов с категориями, что аналогично задаче классификации транзакций по описанию

### Инструкция по загрузке данных

1. Скачайте датасет с Kaggle
2. Распакуйте файл `product_titles.csv` в директорию `data/` проекта
3. Код автоматически определит нужные колонки (поддерживаются: `title`/`product_title`, `category_name`/`category`)
4. При необходимости можно указать маппинг колонок в конфигурационном файле (см. `configs/train_config.yaml`)

## Целевые метрики

### Метрики качества модели

| Метрика | Целевое значение | Описание |
|---------|------------------|----------|
| **Accuracy** | ≥ 90% | Доля корректно классифицированных транзакций |
| **Macro F1-score** | ≥ 0.85 | Среднее F1-score по всем категориям |
| **Weighted F1-score** | ≥ 0.90 | F1-score, взвешенный по частоте категорий |

### Метрики производительности

| Метрика | Целевое значение | Описание |
|---------|------------------|----------|
| **P50 Latency** | ≤ 200 мс | Медианное время ответа API предсказания |
| **P95 Latency** | ≤ 500 мс | 95-й перцентиль времени ответа |
| **P99 Latency** | ≤ 1000 мс | 99-й перцентиль времени ответа |
| **Error Rate** | ≤ 1% | Доля запросов с ошибками (5xx, таймауты) |
| **Model Training Time** | ≤ 30 сек | Время полного переобучения персональной модели |
| **Memory Usage** | ≤ 2 GB на 1000 пользователей | Объем памяти для моделей и данных |

## План экспериментов

### Этап 1: Прототип и базовая архитектура ✅
- [x] Определение архитектуры (ADR-001, ADR-002)
- [x] Реализация Embedding Service на базе `sentence-transformers`
- [x] Реализация User Classifier Service (LogisticRegression/MLP)
- [x] Конфигурационные файлы для обучения
- [x] Скрипт обучения с логированием

### Этап 2: Обучение и валидация ✅
- [x] Загрузка и предобработка данных из Kaggle датасета
- [x] Предобработка данных (нормализация текста, обработка пропусков)
- [x] Конфигурационные файлы для обучения
- [x] Логирование процесса обучения
- [x] Сохранение модели в формате Hugging Face
- [x] Базовая валидация (метрики accuracy, precision, recall, F1)

### Этап 3: Тестирование и CI/CD 🔄
- [x] Покрытие тестами предобработки данных
- [x] Тесты пайплайна обучения
- [x] Проверки формата данных (типы, диапазоны, обязательные поля)
- [x] Тесты API (предсказания, обработка ошибок)
- [x] Настройка GitHub Actions для автоматического запуска тестов
- [x] Линтеры и форматирование кода (black, ruff, mypy)

## Быстрый старт

### Установка зависимостей

Проект использует Poetry для управления зависимостями:

```bash
# Установка Poetry (если еще не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка зависимостей проекта
poetry install
```

### Загрузка данных

1. Скачайте датасет с Kaggle: [Massive Product Text Classification Dataset](https://www.kaggle.com/datasets/asaniczka/product-titles-text-classification/data)
2. Поместите файл `product_titles.csv` в директорию `data/`

### Обучение модели

```bash
# Активация виртуального окружения Poetry
poetry shell

# Запуск обучения с конфигурацией по умолчанию
python -m categoraize.train configs/train_config.yaml

# Запуск с детальным логированием
python -m categoraize.train configs/train_config.yaml --verbose

# Обучение с LogisticRegression
python -m categoraize.train configs/train_config_lr.yaml
```

### Структура проекта

```
CategorAIze/
├── src/
│   └── categoraize/           # Исходный код проекта
│       ├── data/              # Модули для работы с данными
│       │   ├── loader.py      # Загрузка данных
│       │   └── preprocessor.py # Предобработка данных
│       ├── models/            # Модели машинного обучения
│       │   └── classifier.py  # Классификатор продуктов
│       ├── training/           # Модули для обучения
│       │   ├── trainer.py     # Тренер модели
│       │   └── evaluator.py   # Оценка качества модели
│       ├── train.py           # Скрипт для запуска обучения
│       └── predict.py         # Скрипт для офлайн-инференса
├── scripts/                    # Вспомогательные скрипты
│   ├── prepare.py             # Стадия prepare DVC пайплайна
│   ├── evaluate.py            # Стадия evaluate DVC пайплайна
│   └── create_torchserve_archive.sh # Создание TorchServe архива
├── torchserve/                 # TorchServe конфигурация
│   ├── handler.py             # Обработчик запросов
│   └── config.properties      # Конфигурация сервиса
├── tests/                      # Тесты
├── configs/                    # Конфигурационные файлы
│   ├── train_config.yaml       # Конфигурация для MLP
│   └── train_config_lr.yaml   # Конфигурация для LogisticRegression
├── data/                       # Данные (версионируются через DVC)
│   ├── product_titles.csv.dvc # DVC метаданные для датасета
│   └── processed/             # Обработанные данные (выходы prepare)
├── models/                     # Сохраненные модели (версионируются через DVC)
│   └── checkpoint/            # Обученная модель
├── metrics/                    # Метрики (выходы evaluate)
├── model-store/                # TorchServe архивы моделей
├── mlruns/                     # MLflow хранилище экспериментов
├── .dvc/                       # DVC конфигурация
├── dvc.yaml                    # DVC пайплайн
├── dvc.lock                    # DVC lock файл
├── Dockerfile                  # Docker образ для офлайн-инференса
├── Dockerfile.torchserve       # Docker образ для TorchServe
├── .dockerignore              # Исключения для Docker
├── docs/                       # Документация (Markdown)
├── pyproject.toml              # Конфигурация Poetry
└── README.md                   # Этот файл
```

## Воспроизводимость

Для обеспечения воспроизводимости результатов:
- Все случайные операции используют фиксированный `random_seed=42`
- Конфигурация модели хранится в YAML файлах
- Версии зависимостей фиксированы в `pyproject.toml`

## Версионирование данных с DVC

Проект использует DVC (Data Version Control) для версионирования больших файлов (данные и модели), которые не хранятся в Git.

### Физическое расположение данных и моделей

- **Сырой датасет**: `data/product_titles.csv` (версионируется через DVC)
- **Обработанные данные**: `data/processed/` (создаются стадией `prepare`)
- **Обученные модели**: `models/checkpoint/` (версионируется через DVC)
- **Метрики**: `metrics/` (создаются стадией `evaluate`)

### Быстрый старт с DVC

```bash
# Клонирование репозитория
git clone <repository-url>
cd CategorAIze

# Установка зависимостей
poetry install

# Загрузка данных и моделей из DVC
poetry run dvc pull

# Воспроизведение всего пайплайна
poetry run dvc repro
```

### DVC пайплайн

Пайплайн состоит из трёх стадий:

1. **prepare** — предобработка данных и разделение на train/val/test
2. **train** — обучение модели
3. **evaluate** — оценка качества модели

```bash
# Запуск конкретной стадии
poetry run dvc repro prepare
poetry run dvc repro train
poetry run dvc repro evaluate

# Запуск всего пайплайна
poetry run dvc repro

# Просмотр графа зависимостей
poetry run dvc dag
```

### Удалённое хранилище DVC

Настроено локальное хранилище по умолчанию. Для настройки удалённого хранилища (S3, GCS, Azure):

```bash
# Добавление удалённого хранилища
poetry run dvc remote add -d myremote s3://bucket-name/path

# Загрузка данных в удалённое хранилище
poetry run dvc push

# Загрузка данных из удалённого хранилища
poetry run dvc pull
```

### План экспериментов

Каждая версия датасета и модели фиксируется через DVC. Для переключения между версиями:

```bash
# Просмотр истории изменений
git log --oneline

# Переключение на конкретную версию
git checkout <commit-hash>
poetry run dvc checkout
poetry run dvc repro
```

## Трекинг экспериментов с MLflow

Проект использует MLflow для трекинга экспериментов, логирования параметров, метрик и артефактов.

### Запуск MLflow UI

```bash
# Запуск локального UI
poetry run mlflow ui --backend-store-uri mlruns/

# UI будет доступен по адресу: http://localhost:5000
```

### Что логируется в MLflow

Каждый запуск `python -m categoraize.train` создаёт отдельный run с:

- **Параметры**: все параметры из конфигурационного файла
- **Метрики**: accuracy, macro_f1, weighted_f1, mean_confidence (для validation и test)
- **Артефакты**:
  - Обученная модель (classifier)
  - Конфигурационный файл
  - `dvc.lock` (для воспроизводимости)
  - Путь к сохранённой модели

### Связь DVC + MLflow

Для обеспечения связи между данными и экспериментами:

- `dvc.lock` логируется как артефакт в каждом run
- Тег `dvc_pipeline` указывает на использование DVC пайплайна
- Хеши данных и моделей можно отслеживать через `dvc.lock`

### Подключение к удалённому серверу MLflow

Для использования удалённого хранилища (PostgreSQL + S3):

```bash
# Установка переменных окружения
export MLFLOW_TRACKING_URI=postgresql://user:password@host:port/database
export MLFLOW_S3_ENDPOINT_URL=https://s3.amazonaws.com
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Или через конфигурационный файл
poetry run mlflow ui --backend-store-uri postgresql://... --default-artifact-root s3://bucket-name
```

## Docker для офлайн-инференса

Проект включает Docker-образ для выполнения офлайн-инференса модели.

### Сборка образа

```bash
# Сборка образа
docker build -t ml-app:v1 .

# Проверка размера образа (должен быть < 1 ГБ)
docker images ml-app:v1
```

### Запуск контейнера

```bash
# Запуск с монтированием данных
docker run --rm \
  -v $(pwd)/data:/data \
  ml-app:v1 \
  --input_path /data/input.csv \
  --output_path /data/preds.csv \
  --model_path models/checkpoint
```

### Форматы данных

**Входной формат** (CSV):
- Обязательная колонка: `product_title` (названия продуктов)

**Выходной формат** (CSV):
- `product_title` — исходное название продукта
- `predicted_category` — предсказанная категория
- `confidence` — уровень уверенности модели (0.0-1.0)

### Пример использования

```bash
# Подготовка входных данных
echo "product_title
Apple iPhone 13
Samsung Galaxy S21
MacBook Pro" > data/input.csv

# Запуск предсказаний
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/models:/app/models \
  ml-app:v1 \
  --input_path /data/input.csv \
  --output_path /data/preds.csv

# Просмотр результатов
cat data/preds.csv
```

## Развёртывание с TorchServe

Проект поддерживает развёртывание модели как онлайн-сервиса через TorchServe.

### Создание архива модели

```bash
# Создание .mar архива
./scripts/create_torchserve_archive.sh mymodel 1.0 models/checkpoint torchserve/handler.py model-store

# Или вручную
poetry run torch-model-archiver \
  --model-name mymodel \
  --version 1.0 \
  --handler torchserve/handler.py \
  --extra-files models/checkpoint \
  --export-path model-store \
  --force
```

### Сборка Docker образа

```bash
# Сборка образа TorchServe
docker build -f Dockerfile.torchserve -t mymodel-serve:v1 .
```

### Запуск сервиса

```bash
# Запуск контейнера в фоне
docker run -d \
  -p 8080:8080 \
  -p 8081:8081 \
  --name mymodel-serve \
  mymodel-serve:v1

# Проверка статуса
curl http://localhost:8081/ping
```

### REST API

**Предсказание** (POST `/predictions/mymodel`):

```bash
# Пример запроса
curl -X POST http://localhost:8080/predictions/mymodel \
  -H "Content-Type: application/json" \
  -d '{
    "product_titles": ["Apple iPhone 13", "Samsung Galaxy S21"]
  }'
```

**Формат запроса**:
```json
{
  "product_titles": ["название продукта 1", "название продукта 2"]
}
```

**Формат ответа**:
```json
{
  "predictions": [
    {
      "product_title": "Apple iPhone 13",
      "predicted_category": "Electronics",
      "confidence": 0.95
    },
    {
      "product_title": "Samsung Galaxy S21",
      "predicted_category": "Electronics",
      "confidence": 0.92
    }
  ]
}
```

### Управление моделью

```bash
# Регистрация модели
curl -X POST http://localhost:8081/models?url=mymodel.mar

# Просмотр зарегистрированных моделей
curl http://localhost:8081/models

# Удаление модели
curl -X DELETE http://localhost:8081/models/mymodel
```

### Конфигурация сервиса

Параметры настраиваются в `torchserve/config.properties`:

- **Порты**: 8080 (inference), 8081 (management), 8082 (metrics)
- **Количество воркеров**: `workers=1`
- **Максимальный размер батча**: `max_batch_size=32`

## Pre-commit hooks

Pre-commit хуки автоматически проверяют код перед каждым коммитом, запуская линтеры, форматтеры и другие проверки.

### Установка

```bash
# Установите pre-commit (через Poetry, уже включен в dev зависимости)
poetry install

# Или глобально через pip
pip install pre-commit

# Установите хуки в репозиторий
pre-commit install

# Опционально: установите хуки для commit-msg (проверка сообщений коммитов)
pre-commit install --hook-type commit-msg
```

### Использование

После установки хуки будут автоматически запускаться при каждом `git commit`. Если проверки не пройдут, коммит будет отклонен.

```bash
# Запустить проверки вручную для всех файлов
pre-commit run --all-files

# Запустить проверки только для staged файлов
pre-commit run

# Пропустить хуки (не рекомендуется)
git commit --no-verify
```

### Настроенные проверки

- **Ruff** — быстрый линтер и форматтер Python (автоисправление)
- **Black** — форматтер кода (проверка стиля)
- **yamllint** — проверка YAML файлов
- **pre-commit-hooks** — базовые проверки (trailing whitespace, EOF, JSON, TOML, etc.)

Опциональные проверки (закомментированы в `.pre-commit-config.yaml`):
- **isort** — проверка сортировки импортов (ruff тоже проверяет)
- **detect-secrets** — поиск секретов в коде (требует baseline файл)
- **mypy** — проверка типов (может быть медленной)

## Тестирование

```bash
# Запуск всех тестов
poetry run pytest

# Запуск с покрытием кода
poetry run pytest --cov=src/categoraize --cov-report=html

# Запуск конкретного теста
poetry run pytest tests/test_data_loader.py
```

## Проверка качества кода

```bash
# Линтинг
poetry run ruff check src/ tests/

# Форматирование (проверка)
poetry run black --check src/ tests/

# Форматирование (применить)
poetry run black src/ tests/

# Проверка типов
poetry run mypy src/categoraize/ --ignore-missing-imports
```

## Документация

Для локальной разработки документации выполните:

```bash
./scripts/serve-docs.sh
```

Скрипт автоматически:
- Соберёт LikeC4 диаграммы (если установлен Node.js)
- Установит зависимости MkDocs (если нужно)
- Запустит локальный сервер на http://127.0.0.1:8000

## Требования

- **Python 3.11+**
- **Poetry** для управления зависимостями
- **Node.js 20+** (опционально, для LikeC4 диаграмм в документации)

## Подробная документация

- [ADR-001: Глобальная архитектура](docs/adr/001-global-adr.md)
- [ADR-002: ML-модель для персонализированной классификации](docs/adr/002-personalized-classification.md)

(Рекомендую смотреть на [GitHub Pages](https://moneycluster.github.io/CategorAIze/))
