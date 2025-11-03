---
title: Диаграммы LikeC4
---

Здесь отображаются статические артефакты LikeC4, собранные CI и размещённые в этой папке.

Если ниже пусто, значит артефакты ещё не собраны. После первого успешного CI шага «Build LikeC4 (optional)» здесь появится интерактив.

- Гайд по деплою LikeC4: https://likec4.dev/guides/deploy-github-pages/

{{ likec4_iframe('') }}

## Диаграмма из ADR (временно на Mermaid)

```mermaid
flowchart LR
  A[API Layer (FastAPI)] --> E[Embedding Service]
  A --> U[User Classifier Service]
  A --> F[Feedback Loop]
  U --|reads/writes|--> S[(Storage)]
  F --|append training data|--> S
  E --> U
  classDef svc fill:#e5f0ff,stroke:#3166d9,stroke-width:1px,color:#000
  class A,E,U,F svc
  class S fill:#fff3cd,stroke:#997404
```


