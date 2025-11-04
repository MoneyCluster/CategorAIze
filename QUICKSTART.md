# Быстрый старт

## Установка

1. Установите Poetry (если еще не установлен):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Клонируйте репозиторий и установите зависимости:
```bash
git clone <repository-url>
cd CategorAIze
poetry install
```

## Подготовка данных

1. Скачайте датасет с Kaggle:
   - Перейдите на [Massive Product Text Classification Dataset](https://www.kaggle.com/datasets/asaniczka/product-titles-text-classification/data)
   - Скачайте файл `product_titles.csv`

2. Поместите файл в директорию `data/`:
```bash
mkdir -p data
# Поместите product_titles.csv в data/
```

## Обучение модели

### Базовое обучение

```bash
poetry shell
python -m categoraize.train configs/train_config.yaml
```

### С детальным логированием

```bash
python -m categoraize.train configs/train_config.yaml --verbose
```

### Обучение с LogisticRegression

```bash
python -m categoraize.train configs/train_config_lr.yaml
```

## Запуск тестов

```bash
# Все тесты
poetry run pytest

# С покрытием кода
poetry run pytest --cov=src/categoraize --cov-report=html

# Конкретный тест
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

## Структура конфигурационного файла

Конфигурационный файл содержит следующие секции:

- `data`: Настройки данных (путь, имя файла)
- `preprocessing`: Настройки предобработки (lowercase, remove_punctuation)
- `split`: Настройки разделения данных (test_size, val_size, random_seed)
- `model`: Настройки модели (embedding_model_name, classifier_type, classifier_params)
- `output`: Путь для сохранения модели

## Воспроизводимость

Все случайные операции используют фиксированный `random_seed=42` для обеспечения воспроизводимости результатов.

## Получение помощи

```bash
python -m categoraize.train --help
```

