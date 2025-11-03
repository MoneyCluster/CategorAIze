---
title: ADR-001 Персонализированная классификация трат пользователей
sidebar_label: ADR-001
---

**Status:** Accepted

**Date:** 2025-11-01

**Version:** 1.0

---

## **Business Goal**

**Цель проекта:** Разработать систему автоматической классификации финансовых трат пользователей по персонализированным категориям с возможностью обучения на основе обратной связи.

**Проблема:** Пользователи ведут учет финансов, загружая чеки и транзакции. Ручная категоризация занимает много времени. Каждый пользователь использует свои категории (например, один может использовать "Продукты" и "Кафе", другой — "Еда дома" и "Рестораны"), что делает невозможным использование единой глобальной модели классификации.

**Решение:** Персонализированные ML-модели для каждого пользователя, обучаемые на его исторических данных с возможностью улучшения через обратную связь.

---

## **Target Metrics**

### Бизнес-метрики

| Метрика | Целевое значение | Описание |
|---------|------------------|----------|
| **Точность классификации** | ≥ 90% | Доля корректно классифицированных трат пользователем |
| **Скорость внедрения категорий** | ≤ 5 примеров | Количество примеров для обучения новой категории |

### Технические метрики

| Метрика | Целевое значение | Описание |
|---------|------------------|----------|
| **Среднее время отклика API** | ≤ 200 мс | Время обработки запроса классификации (p50) |
| **P95 время отклика** | ≤ 500 мс | 95-й перцентиль времени ответа |
| **Доля неуспешных запросов** | ≤ 1% | Процент запросов с ошибками (5xx, таймауты) |
| **Использование памяти** | ≤ 2 GB на 1000 пользователей | Объем памяти для моделей и данных |
| **Время обучения модели** | ≤ 30 сек на пользователя | Время полного переобучения персональной модели |

---

## **Context**

Приложение должно автоматически классифицировать пользовательские траты по категориям (например: *еда, транспорт, подписки*).
Однако, в отличие от типовых задач, категории не фиксированы:

* Каждый пользователь задаёт собственные категории;
* Пользователь может изменять категории и переопределять результаты классификации.

**Workflow:**

1. **Загрузка данных:** Пользователь загружает чеки/транзакции (текстовые описания трат)
2. **Автоклассификация:** Система автоматически предлагает категорию на основе описания
3. **Обратная связь:** Пользователь может скорректировать категорию, если предсказание неверно
4. **Дообучение:** Система периодически переобучает персональную модель на основе всех данных пользователя (включая правки)

Это делает невозможным использование одной глобальной ML-модели.
Необходима архитектура, поддерживающая **массовую персонализацию** с низкими затратами на хранение и обучение.

---

## **System Architecture (UML)**

### Component Diagram

```plantuml
@startuml
!theme plain
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF

package "Frontend Layer" {
  package "Web Application" {
    component [UI Components] as UI
    component [API Client] as Client
  }
  component [Web Application] as Web
  component [Mobile App] as Mobile
}

package "API Layer" {
  package "FastAPI Gateway" {
    component [Upload Endpoint] as Upload
    component [Predict Endpoint] as Predict
    component [Feedback Endpoint] as Feedback
    component [Train Endpoint] as Train
  }
  component [FastAPI Gateway] as API
}

package "Business Logic Layer" {
  component [Transaction Service] as TransService
  component [Category Service] as CatService
  component [Model Service] as ModelService
  component [Feedback Loop Service] as FeedbackService
}

package "ML Services Layer" {
  component [Embedding Service] as Embedding
  note right of Embedding : Общая LLM-модель\n(sentence-transformers)\nall-MiniLM-L6-v2
  component [User Classifier Service] as Classifier
  note right of Classifier : Персональный\nклассификатор\n(scikit-learn)\nдля каждого пользователя
  component [Training Scheduler] as Scheduler
}

package "Data Layer" {
  database "PostgreSQL/SQLite" as DB
  storage "Model Storage (S3/Local)" as ModelStorage
}

' Frontend connections
Web --> API : HTTPS/REST
Mobile --> API : HTTPS/REST
UI --> Client
Client --> API

' API to Business Logic
API --> TransService
API --> CatService
API --> ModelService
API --> FeedbackService

Upload --> TransService
Predict --> ModelService
Feedback --> FeedbackService
Train --> ModelService

' Business Logic to ML Services
ModelService --> Embedding : get_embedding(text)
ModelService --> Classifier : predict(embedding)
ModelService --> Classifier : train(user_data)
FeedbackService --> Classifier : trigger_retraining()
Scheduler --> ModelService : periodic_retraining()

' Business Logic to Data Layer
TransService --> DB : CRUD transactions
CatService --> DB : CRUD categories
ModelService --> DB : read training data
ModelService --> ModelStorage : save/load models
FeedbackService --> DB : save feedback

' ML Services to Data Layer
Classifier --> Embedding : use embeddings
Classifier --> ModelStorage : load/save model
Classifier --> DB : read training data

@enduml
```

### Sequence Diagram: Transaction Classification Flow

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

actor User
participant "Web App" as Web
participant "API Gateway" as API
participant "Transaction Service" as TransSvc
participant "Model Service" as ModelSvc
participant "Embedding Service" as Embedding
participant "User Classifier" as Classifier
participant "Database" as DB
participant "Model Storage" as Storage

== Upload Transaction ==
User -> Web: Upload receipt/transaction
Web -> API: POST /upload
activate API
API -> TransSvc: save_transaction(user_id, description, amount)
activate TransSvc
TransSvc -> DB: INSERT transaction
activate DB
DB --> TransSvc: transaction_id
deactivate DB
deactivate TransSvc
API --> Web: {transaction_id, status: "saved"}
deactivate API
Web --> User: Transaction saved

== Predict Category ==
User -> Web: Request category prediction
Web -> API: POST /predict {transaction_id}
activate API
API -> TransSvc: get_transaction(transaction_id)
activate TransSvc
TransSvc -> DB: SELECT transaction
activate DB
DB --> TransSvc: transaction data
deactivate DB
deactivate TransSvc

API -> ModelSvc: predict_category(user_id, description)
activate ModelSvc

ModelSvc -> Embedding: get_embedding(description)
activate Embedding
Embedding --> ModelSvc: embedding_vector[384]
deactivate Embedding

ModelSvc -> Storage: load_user_model(user_id)
activate Storage
Storage --> ModelSvc: user_classifier_model
deactivate Storage

ModelSvc -> Classifier: predict(embedding, model)
activate Classifier
Classifier --> ModelSvc: {category_id, confidence}
deactivate Classifier

ModelSvc -> DB: get_category_name(category_id)
activate DB
DB --> ModelSvc: category_name
deactivate DB

deactivate ModelSvc
API --> Web: {category_id, category_name, confidence}
deactivate API
Web --> User: Display predicted category

== User Feedback ==
User -> Web: Correct category (if wrong)
Web -> API: POST /feedback {transaction_id, correct_category_id}
activate API
API -> FeedbackService: save_feedback(transaction_id, correct_category_id)
activate FeedbackService
FeedbackService -> DB: UPDATE transaction category
activate DB
FeedbackService -> Embedding: get_embedding(transaction.description)
activate Embedding
Embedding --> FeedbackService: embedding_vector
deactivate Embedding
FeedbackService -> DB: INSERT training_data(embedding, category)
DB --> FeedbackService: success
deactivate DB
FeedbackService -> ModelSvc: trigger_retraining(user_id)
activate ModelSvc
ModelSvc -> DB: get_all_training_data(user_id)
activate DB
DB --> ModelSvc: training_dataset
deactivate DB
ModelSvc -> Classifier: train(dataset)
activate Classifier
Classifier --> ModelSvc: trained_model
deactivate Classifier
ModelSvc -> Storage: save_model(user_id, model)
activate Storage
Storage --> ModelSvc: saved
deactivate Storage
deactivate ModelSvc
deactivate FeedbackService
API --> Web: {status: "feedback_saved", "retraining_triggered"}
deactivate API
Web --> User: Category updated, model will retrain

@enduml
```

### Class Diagram: Core Domain Entities

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

class User {
  - id: UUID
  - email: String
  - created_at: DateTime
  + get_transactions(): List[Transaction]
  + get_categories(): List[Category]
  + get_model(): UserClassifierModel
}

class Transaction {
  - id: UUID
  - user_id: UUID
  - description: String
  - amount: Decimal
  - category_id: UUID
  - embedding: Vector[384]
  - created_at: DateTime
  + predict_category(): Category
  + update_category(category_id: UUID): void
  + to_training_sample(): TrainingData
}

class Category {
  - id: UUID
  - user_id: UUID
  - name: String
  - created_at: DateTime
  + get_transactions(): List[Transaction]
}

class TrainingData {
  - id: UUID
  - user_id: UUID
  - embedding: Vector[384]
  - category_id: UUID
  - created_at: DateTime
}

class UserClassifierModel {
  - user_id: UUID
  - model_type: String
  - parameters: Dict
  - accuracy: Float
  - trained_at: DateTime
  - model_path: String
  + predict(embedding: Vector): Tuple[Category, Float]
  + train(dataset: List[TrainingData]): void
  + save(path: String): void
  + load(path: String): UserClassifierModel
}

class EmbeddingModel {
  - model_name: String
  - version: String
  - dimension: Int = 384
  + encode(text: String): Vector[384]
  + encode_batch(texts: List[String]): List[Vector[384]]
}

' Relationships
User "1" *-- "many" Transaction : has
User "1" *-- "many" Category : defines
User "1" -- "1" UserClassifierModel : owns
Category "1" *-- "many" Transaction : categorizes
Transaction "1" -- "0..1" TrainingData : converts to
UserClassifierModel "1" *-- "many" TrainingData : trained on
UserClassifierModel ..> EmbeddingModel : uses

note right of UserClassifierModel
  Персональный классификатор
  для каждого пользователя.
  Использует общий EmbeddingModel
  для получения эмбеддингов.
end note

note right of EmbeddingModel
  Общая модель эмбеддингов
  для всех пользователей.
  Не требует переобучения.
end note

@enduml
```

### Deployment Diagram: System Infrastructure

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

node "Client Devices" {
  [Web Browser] as Browser
  [Mobile App] as MobileApp
}

cloud "CDN / Load Balancer" as CDN

node "Web Server" {
  [Web Application\n(React/Vue)] as WebApp
  [Static Assets] as Static
}

node "API Server" {
  [FastAPI Application] as FastAPI
  [Uvicorn ASGI Server] as Uvicorn
}

node "ML Services Cluster" {
  [Embedding Service\n(Single Instance)] as EmbedSvc
  [Classifier Service\n(Multiple Instances)] as ClassifierSvc1
  [Classifier Service\n(Multiple Instances)] as ClassifierSvc2
}

node "Database Server" {
  database "PostgreSQL" as PG {
    [Transaction Data]
    [User Data]
    [Category Data]
    [Training Data]
  }
}

node "Model Storage" {
  storage "S3 / Local FS" as Storage {
    [User Models\n(joblib/pickle)]
  }
}

node "Background Workers" {
  [Training Scheduler] as Scheduler
  [Retraining Queue] as Queue
}

Browser --> CDN : HTTPS
MobileApp --> CDN : HTTPS
CDN --> WebApp : HTTP
WebApp --> FastAPI : REST API
FastAPI --> EmbedSvc : gRPC / HTTP
FastAPI --> ClassifierSvc1 : gRPC / HTTP
FastAPI --> ClassifierSvc2 : gRPC / HTTP
FastAPI --> PG : SQL
ClassifierSvc1 --> Storage : Read/Write models
ClassifierSvc2 --> Storage : Read/Write models
Scheduler --> FastAPI : Trigger retraining
Scheduler --> Queue : Queue training jobs
Queue --> ClassifierSvc1 : Training tasks
Queue --> ClassifierSvc2 : Training tasks

note right of EmbedSvc
  Общий эмбеддер
  для всех пользователей
end note

note right of ClassifierSvc1
  Персональные классификаторы
  масштабируются горизонтально
end note

@enduml
```

