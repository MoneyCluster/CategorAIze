---
title: ADR-001 Персонализированная классификация трат пользователей
sidebar_label: ADR-001
---

**Status:** Accepted

**Date:** 2025-11-01

**Version:** 1.0

---

## **Business Goal**

**Цель проекта:** Разработать систему учета финансов (доходы, расходы, перемещения) минимизируя число ручных операций со стороны человека

**Проблема:** Пользователи ведут учет финансов, загружая чеки и транзакции. Ручная категоризация занимает много времени. Каждый пользователь использует свои категории (например, один может использовать "Продукты" и "Кафе", другой — "Еда дома" и "Рестораны"), что делает невозможным использование единой глобальной модели классификации.

**Решение:** Персонализированные ML-модели для каждого пользователя, обучаемые на его исторических данных с возможностью улучшения через обратную связь.

---

## **Контекст**

В данном документе предлагается определиться с дальнейшей схемой архитектуры системы. Основная задача - минимизировать число ручных операций со стороны человека при вводе данных.

Для начала необходимо определиться с тем, какие данные будут вводиться в систему.

### Данные

- Доходы
- Расходы
- Перемещения

Операции расходов и доходов могут иметь категории, которые будут использоваться для классификации. Категория может быть вложенной и иметь родительскую категорию.

## Архитектура (UML)

### Сущности системы

Ниже представлено детальное описание сущностей системы с полями базы данных. Описание соответствует ERD диаграмме и включает все необходимые поля для реализации системы.

??? note "DBML схема базы данных"
    ```dbml
    // Use DBML to define your database structure
    // Docs: https://dbml.dbdiagram.io/docs

    Table users {
      id uuid [primary key]
      email varchar(255) [not null, unique, note: 'Email адрес пользователя']
      password_hash varchar(255) [not null, note: 'Хеш пароля (bcrypt)']
      full_name varchar(255)
      is_active boolean [not null, default: true]
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      last_login_at timestamp
      settings jsonb [note: 'JSON объект с настройками пользователя']
      
      indexes {
        email [unique]
        created_at
      }
    }

    Table accounts {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя-владельца']
      name varchar(255) [not null, note: 'Название счета']
      type varchar(50) [note: 'Тип счета: bank, cash, card, wallet']
      currency varchar(3) [not null, default: 'RUB', note: 'Код валюты (ISO 4217)']
      balance decimal(15,2) [not null, default: 0, note: 'Текущий баланс счета']
      is_active boolean [not null, default: true]
      sort_order integer [not null, default: 0]
      metadata jsonb [note: 'Дополнительные метаданные']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        (user_id, is_active) [note: 'where is_active = true']
      }
    }

    Table categories {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя-владельца']
      name varchar(255) [not null, note: 'Название категории']
      parent_id uuid [ref: > categories.id, note: 'Идентификатор родительской категории']
      type varchar(20) [not null, note: 'income или expense']
      color varchar(7) [note: 'Цвет категории в HEX формате']
      icon varchar(50) [note: 'Название иконки для UI']
      description text
      is_active boolean [not null, default: true]
      sort_order integer [not null, default: 0]
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        parent_id
        (user_id, type)
      }
    }

    Table transactions {
      id uuid [primary key]
      account_id uuid [not null, ref: > accounts.id, note: 'Идентификатор счета']
      type varchar(20) [not null, note: 'income или expense']
      amount decimal(15,2) [not null, note: 'Сумма транзакции']
      currency varchar(3) [not null, default: 'RUB', note: 'Код валюты (ISO 4217)']
      description text [not null, note: 'Текстовое описание транзакции']
      category_id uuid [ref: > categories.id, note: 'Идентификатор категории']
      transaction_date date [not null, note: 'Дата фактического совершения транзакции']
      source varchar(100) [note: 'Источник данных: receipt, bank_statement, manual']
      external_id varchar(255) [note: 'Внешний идентификатор']
      metadata jsonb [note: 'Дополнительные метаданные']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        account_id
        category_id
        transaction_date [note: 'DESC']
        type
        (external_id) [note: 'where external_id is not null']
      }
    }

    Table transfers {
      id uuid [primary key]
      from_account_id uuid [not null, ref: > accounts.id, note: 'Счет-источник']
      to_account_id uuid [not null, ref: > accounts.id, note: 'Счет-назначение']
      amount decimal(15,2) [not null, note: 'Сумма перемещения']
      currency varchar(3) [not null, default: 'RUB', note: 'Код валюты']
      description text
      transfer_date date [not null, note: 'Дата перемещения']
      fee decimal(15,2) [note: 'Комиссия за перемещение']
      fee_category_id uuid [ref: > categories.id, note: 'Категория для комиссии']
      metadata jsonb [note: 'Дополнительные метаданные']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        from_account_id
        to_account_id
        (transfer_date) [note: 'DESC']
      }
    }
    ```

---

![ERD Global](../data/images/moneycluster_erd_global.svg)


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

