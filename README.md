# CategorAIze

Документация проекта размещена на [GitHub Pages](https://moneycluster.github.io/CategorAIze/).

## Быстрый старт

Для локальной разработки документации выполните:

```bash
./scripts/serve-docs.sh
```

Скрипт автоматически:
- Соберёт LikeC4 диаграммы (если установлен Node.js)
- Установит зависимости MkDocs (если нужно)
- Запустит локальный сервер на http://127.0.0.1:8000

## Структура проекта

```
CategorAIze/
├── docs/                    # Документация (Markdown)
│   ├── _likec4/            # Исходники LikeC4 диаграмм
│   ├── _macros/            # Макросы для MkDocs
│   ├── architecture/       # Архитектурная документация
│   └── guides/             # Руководства
├── scripts/                 # Скрипты для разработки
│   ├── serve-docs.sh      # Запуск локального сервера
│   └── build-likec4.sh    # Сборка LikeC4 диаграмм
├── mkdocs.yml              # Конфигурация MkDocs
└── .github/workflows/      # CI/CD для GitHub Pages
```

## Требования

- **Python 3.11+** для MkDocs
- **Node.js 20+** (опционально, для LikeC4 диаграмм)

## Полезные команды

```bash
# Запуск локального сервера (основная команда)
./scripts/serve-docs.sh

# Варианты использования
./scripts/serve-docs.sh                    # Стандартный запуск
./scripts/serve-docs.sh --skip-likec4       # Без сборки LikeC4
./scripts/serve-docs.sh --port 9000         # На другом порту

# Только сборка LikeC4 диаграмм
./scripts/build-likec4.sh
```

## Подробная документация

- [Как вносить изменения в документацию](docs/guides/contributing.md)
- [Локальная разработка](docs/guides/local-setup.md)
- [Стиль документации](docs/guides/style.md)

