---
title: Архитектура — обзор
---

Короткий обзор архитектуры. Встроенная LikeC4-диаграмма:

{{ likec4_view('CategorAIze', 'landscape') }}

Если интерактив ещё не собран CI, ниже fallback на Mermaid:

```mermaid
flowchart LR
  A[API Layer (FastAPI)] --> E[Embedding Service]
  A --> U[User Classifier Service]
  A --> F[Feedback Loop]
  U --|reads/writes|--> S[(Storage)]
  F --|append training data|--> S
  E --> U
```


