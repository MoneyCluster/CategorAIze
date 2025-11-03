---
title: Как вносить изменения
---

## Добавление новой страницы документации

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

### 4. Добавьте LikeC4 диаграмму (опционально)

Если нужно встроить диаграмму LikeC4, используйте макрос:

```markdown
## Архитектура компонента

{{ likec4_view('CategorAIze', 'landscape') }}
```

**Параметры макроса:**
- `'CategorAIze'` — имя проекта (из `likec4.config.ts`)
- `'landscape'` — имя view (из файла `.c4`)
- Третий параметр (опционально) — высота iframe: `'80vh'`

## Добавление новой LikeC4 диаграммы

### 1. Создайте файл модели

Создайте файл в `docs/_likec4/` с расширением `.c4`:

```bash
docs/_likec4/my-diagram.c4
```

### 2. Опишите модель

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

### 3. Пересоберите диаграммы

```bash
./scripts/build-likec4.sh
```

### 4. Используйте в документации

```markdown
{{ likec4_view('CategorAIze', 'overview') }}
```

**Важно:** Имя view должно совпадать с именем в блоке `views {}` в файле `.c4`.

## Работа с макросами

### Доступные макросы

- `{{ likec4_view('project', 'view', '70vh') }}` — встраивание конкретного view
- `{{ likec4_iframe('') }}` — встраивание главной страницы LikeC4

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

## Полезные ссылки

- [Локальная разработка](./local-setup.md) — подробности по настройке окружения
- [Стиль документации](./style.md) — рекомендации по оформлению
- [LikeC4 документация](https://likec4.dev) — официальная документация LikeC4


