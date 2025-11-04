---
title: Работа с документацией
---

# Работа с документацией

Этот документ описывает, как работать с документацией проекта CategorAIze: как добавить страницу, настроить окружение, использовать диаграммы и многое другое.

## Быстрый старт

### Предварительные требования

- **Python 3.11+** (для MkDocs)
- **Node.js 20+** (для LikeC4, опционально)
- **Git** (для работы с репозиторием)

### Установка и запуск

```bash
# Установка зависимостей
python3 -m pip install --upgrade pip
pip install mkdocs-material mkdocs-macros-plugin mkdocs-include-markdown-plugin

# Запуск локального сервера (основная команда)
./scripts/serve-docs.sh
```

Документация будет доступна по адресу: http://127.0.0.1:8000/

Сервер автоматически перезагружает страницы при изменении файлов в `docs/`.

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
├── adr/              # Architecture Decision Records
├── architecture/     # Архитектурная документация
├── guides/           # Руководства
├── likec4/           # Страница для просмотра диаграмм
└── *.md              # Основные страницы
```

## Добавление новой страницы

### 1. Создайте Markdown файл

Создайте файл в соответствующей папке `docs/`:

```bash
# Например, новая страница в разделе "Архитектура"
docs/architecture/my-feature.md
```

### 2. Добавьте frontmatter

В начале файла добавьте метаданные:

```markdown
---
title: Название страницы
sidebar_label: Короткое название
sidebar_position: 2  # Порядок в меню (необязательно)
---

Содержимое страницы...
```

### 3. Добавьте в навигацию

Откройте `mkdocs.yml` и добавьте страницу в секцию `nav`:

```yaml
nav:
  - Архитектура:
      - Обзор: architecture/overview.md
      - Моя фича: architecture/my-feature.md  # ← добавьте здесь
```

## Работа с LikeC4 диаграммами

### Сборка диаграмм

**Рекомендуется использовать скрипт:**

```bash
./scripts/build-likec4.sh
```

**Или вручную:**

```bash
# Собрать LikeC4 артефакты
npx --yes likec4@latest build --config docs/_likec4/likec4.config.ts --output dist-likec4

# Скопировать в статику
rm -rf docs/_static/likec4
mkdir -p docs/_static/likec4
cp -R dist-likec4/* docs/_static/likec4/
rm -rf dist-likec4
```

### Добавление новой диаграммы

1. Создайте файл `docs/_likec4/название.c4`
2. Опишите модель в синтаксисе LikeC4
3. Соберите (см. выше) или используйте fallback на Mermaid для разработки

Минимальный пример:

```likec4
specification {
  system
}

model MyProject {
  system api "API Service"
  system db "Database"

  relationship api -> db "Reads/Writes"
}

views {
  overview {
    include *
    layout lr
  }
}
```

### Использование в документации

В любом `.md` файле можно использовать макрос:

```markdown
{{ likec4_view('CategorAIze', 'landscape') }}
```

**Параметры макроса:**
- `'CategorAIze'` — имя проекта (из `likec4.config.ts`)
- `'landscape'` — имя view (из файла `.c4`)
- Третий параметр (опционально) — высота iframe: `'80vh'`

## Стиль документации

- Пишите коротко, задача на странице — одна
- Первым делом — контекст, далее шаги
- Диаграммы: `{{ likec4_view('...') }}` для LikeC4, либо Mermaid
- Длинные блоки кода — со свёрткой (Material > details)

Пример использования details:

```markdown
??? note "Подробности"
    Дополнительная информация здесь.
```

??? note "Подробности"
    Дополнительная информация здесь.

## Работа с макросами

### Доступные макросы

Доступны два макроса для встраивания LikeC4 диаграмм:

**Встраивание конкретного view:**
```markdown
{{ likec4_view('project', 'view', '70vh') }}
```

**Встраивание главной страницы LikeC4:**
```markdown
{{ likec4_iframe('') }}
```

### Добавление нового макроса

Макросы определены в `docs/_macros/main.py`. Пример:

```python
def my_macro(param: str) -> str:
    return f"<div>Результат: {param}</div>"

env.macro(my_macro)
```

## Проверка перед коммитом

### 1. Соберите LikeC4 (если изменяли модели)

```bash
./scripts/build-likec4.sh
```

### 2. Запустите локальный сервер

```bash
./scripts/serve-docs.sh
```

### 3. Проверьте визуально

Откройте http://127.0.0.1:8000 и проверьте:
- ✅ Страницы открываются
- ✅ LikeC4 диаграммы отображаются
- ✅ Навигация работает
- ✅ Нет ошибок в консоли браузера

### 4. Проверьте сборку

```bash
python3 -m mkdocs build
# Убедитесь, что нет ошибок
```

## Публикация

После коммита и push в ветку `main`:
1. GitHub Actions автоматически соберёт документацию
2. Опубликует на GitHub Pages
3. Доступна по адресу: https://moneycluster.github.io/CategorAIze/

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

## Полезные ссылки

- [LikeC4 документация](https://likec4.dev) — официальная документация LikeC4
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) — документация темы
