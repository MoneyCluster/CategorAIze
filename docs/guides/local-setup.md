---
title: Локальная разработка документации
---

## Предварительные требования

- **Python 3.11+** (для MkDocs)
- **Node.js 20+** (для LikeC4, опционально)
- **Git** (для работы с репозиторием)

## Быстрый старт

### 1. Установка зависимостей

```bash
# Установка MkDocs и плагинов
python3 -m pip install --upgrade pip
pip install mkdocs-material mkdocs-macros-plugin mkdocs-include-markdown-plugin
```

### 2. Локальный просмотр документации

```bash
# Из корня репозитория
python3 -m mkdocs serve
```

Документация будет доступна по адресу: http://127.0.0.1:8000/

Сервер автоматически перезагружает страницы при изменении файлов в `docs/`.

## Работа с LikeC4 диаграммами

### Сборка диаграмм

**Вариант 1: Использовать скрипт (рекомендуется)**

```bash
./scripts/build-likec4.sh
```

**Вариант 2: Вручную**

```bash
# Собрать LikeC4 артефакты
npx --yes likec4@latest build --config docs/_likec4/likec4.config.ts --output dist-likec4

# Скопировать в статику (чтобы макросы работали)
rm -rf docs/_static/likec4
mkdir -p docs/_static/likec4
cp -R dist-likec4/* docs/_static/likec4/
rm -rf dist-likec4
```

После этого макросы `{{ likec4_iframe('') }}` в Markdown-файлах будут отображать диаграммы.

### Структура LikeC4

- **Модели**: `docs/_likec4/*.c4` — файлы с диаграммами
- **Конфиг**: `docs/_likec4/likec4.config.ts` — конфигурация проекта
- **Артефакты**: `docs/_static/likec4/` — собранные статические файлы (в gitignore)

### Добавление новой диаграммы

1. Создайте файл `docs/_likec4/название.c4`
2. Опишите модель в синтаксисе LikeC4
3. Соберите (см. выше) или используйте fallback на Mermaid для разработки

## Использование макросов

В любом `.md` файле можно использовать:

```markdown
{{ likec4_iframe('') }}              # Главная страница LikeC4
{{ likec4_iframe('views/landscape') }}  # Конкретное представление
```

Макросы определены в `docs/_macros/main.py`.

## Проверка перед коммитом

```bash
# 1. Собрать LikeC4 (если изменяли модели)
npx --yes likec4@latest build --config docs/_likec4/likec4.config.ts --output dist-likec4
# ... копировать в docs/_static/likec4 (см. выше)

# 2. Проверить сборку MkDocs
python3 -m mkdocs build

# 3. Запустить локальный сервер и проверить визуально
python3 -m mkdocs serve
```

## Структура проекта

```
docs/
├── _assets/          # JS/CSS для Mermaid и других
├── _likec4/          # Исходники LikeC4 (модели + конфиг)
│   ├── *.c4          # Модели диаграмм
│   └── likec4.config.ts
├── _macros/          # Python макросы для MkDocs
│   └── main.py
├── _static/          # Статические артефакты (в gitignore)
│   └── likec4/       # Собранные LikeC4 файлы
├── architecture/     # Архитектурная документация
├── guides/           # Руководства
├── likec4/           # Страница для просмотра диаграмм
└── *.md              # Основные страницы
```

## Устранение проблем

### Макросы не работают

- Убедитесь, что `docs/_macros/__init__.py` существует
- Проверьте `mkdocs.yml` — плагин `macros` должен быть настроен

### LikeC4 не отображается

- Убедитесь, что собрали диаграммы и скопировали в `docs/_static/likec4/`
- Проверьте консоль браузера на ошибки загрузки iframe

### MkDocs не запускается

- Проверьте версию Python: `python3 --version` (нужна 3.11+)
- Переустановите зависимости: `pip install --upgrade mkdocs-material mkdocs-macros-plugin`

