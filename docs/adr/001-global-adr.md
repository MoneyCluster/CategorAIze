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

## Архитектура

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
      parent_account_id uuid [ref: > accounts.id, note: 'Родительский счет (для иерархии: банк -> счет)']
      name varchar(255) [not null, note: 'Название счета']
      type varchar(50) [note: 'Тип счета: bank, cash, card, wallet']
      currency varchar(3) [not null, default: 'RUB', note: 'Код валюты (ISO 4217)']
      balance decimal(15,2) [not null, default: 0, note: 'Текущий баланс счета (вычисляемое или кэш)']
      is_active boolean [not null, default: true]
      sort_order integer [not null, default: 0]
      metadata jsonb [note: 'Дополнительные метаданные']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        parent_account_id
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

    Table stores {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      name varchar(255) [not null, note: 'Название магазина/торговой точки']
      address text [note: 'Адрес магазина']
      metadata jsonb [note: 'Дополнительные метаданные (координаты, телефон и т.д.)']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        (user_id, name)
      }
    }

    Table receipts {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      store_id uuid [ref: > stores.id, note: 'Идентификатор магазина']
      file_path varchar(500) [not null, note: 'Путь к файлу чека']
      file_name varchar(255) [not null, note: 'Имя файла']
      file_size bigint [not null, note: 'Размер файла в байтах']
      mime_type varchar(100) [note: 'MIME тип файла']
      ocr_text text [note: 'Текст, извлеченный из чека (OCR)']
      extracted_data jsonb [note: 'Структурированные данные из чека (сумма, дата, товары)']
      receipt_date date [note: 'Дата чека (извлеченная из OCR)']
      total_amount decimal(15,2) [note: 'Общая сумма чека']
      processing_status varchar(50) [not null, default: 'pending', note: 'pending, processing, completed, failed']
      uploaded_at timestamp [not null, default: `now()`]
      processed_at timestamp
      created_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        store_id
        receipt_date
        processing_status
      }
    }

    Table transaction_groups {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      receipt_id uuid [ref: > receipts.id, note: 'Связь с чеком (если группа создана из чека)']
      store_id uuid [ref: > stores.id, note: 'Идентификатор магазина']
      name varchar(255) [note: 'Название группы (например, "Покупка в магазине X")']
      total_amount decimal(15,2) [note: 'Общая сумма группы']
      transaction_date date [not null, note: 'Дата транзакций в группе']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        receipt_id
        store_id
        transaction_date
      }
    }

    Table transactions {
      id uuid [primary key]
      account_id uuid [not null, ref: > accounts.id, note: 'Идентификатор счета']
      transaction_group_id uuid [ref: > transaction_groups.id, note: 'Группа транзакций (чек может содержать несколько позиций)']
      type varchar(20) [not null, note: 'income или expense']
      amount decimal(15,2) [not null, note: 'Сумма транзакции']
      currency varchar(3) [not null, default: 'RUB', note: 'Код валюты (ISO 4217)']
      description text [not null, note: 'Текстовое описание транзакции']
      category_id uuid [ref: > categories.id, note: 'Идентификатор категории (проставленная пользователем)']
      predicted_category_id uuid [ref: > categories.id, note: 'Предсказанная категория (из ML модели)']
      transaction_date date [not null, note: 'Дата фактического совершения транзакции']
      source varchar(100) [note: 'Источник данных: receipt, bank_statement, manual']
      external_id varchar(255) [note: 'Внешний идентификатор']
      comment text [note: 'Комментарий пользователя к транзакции']
      metadata jsonb [note: 'Дополнительные метаданные']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        account_id
        transaction_group_id
        category_id
        predicted_category_id
        transaction_date [note: 'DESC']
        type
        (external_id) [note: 'where external_id is not null']
      }
    }

    Table tags {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      name varchar(100) [not null, note: 'Название тега']
      color varchar(7) [note: 'Цвет тега в HEX формате']
      created_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        (user_id, name) [unique]
      }
    }

    Table transaction_tags {
      transaction_id uuid [ref: > transactions.id, note: 'Идентификатор транзакции']
      tag_id uuid [ref: > tags.id, note: 'Идентификатор тега']
      
      indexes {
        (transaction_id, tag_id) [unique]
        transaction_id
        tag_id
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

    Table training_data {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      transaction_id uuid [ref: > transactions.id, note: 'Связь с исходной транзакцией']
      embedding vector(384) [not null, note: 'Векторное представление описания (эмбеддинг размерностью 384)']
      category_id uuid [not null, ref: > categories.id, note: 'Правильная категория (ground truth)']
      source varchar(50) [not null, default: 'user_feedback', note: 'Источник: user_feedback, manual, auto_confirmed']
      confidence_threshold decimal(5,4) [note: 'Минимальный порог уверенности (если был)']
      is_validated boolean [not null, default: true, note: 'Флаг валидации данных']
      created_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        transaction_id
        category_id
        (user_id, category_id)
      }
    }

    Table user_classifier_models {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, unique, note: 'Идентификатор пользователя (один пользователь - одна активная модель)']
      model_type varchar(50) [not null, default: 'LogisticRegression', note: 'Тип модели: LogisticRegression, MLPClassifier, SVM']
      model_version varchar(20) [not null, default: '1.0', note: 'Версия модели']
      model_path varchar(500) [not null, note: 'Путь к файлу модели в хранилище (S3 или локальная ФС)']
      embedding_model_name varchar(100) [not null, default: 'sentence-transformers/all-MiniLM-L6-v2', note: 'Название модели эмбеддингов']
      embedding_dimension integer [not null, default: 384, note: 'Размерность векторов эмбеддингов']
      parameters jsonb [note: 'Гиперпараметры модели (C, max_iter и т.д.)']
      training_samples_count integer [not null, default: 0, note: 'Количество примеров для обучения']
      accuracy decimal(5,4) [note: 'Метрика точности модели']
      precision decimal(5,4) [note: 'Метрика precision (макро-усредненная)']
      recall decimal(5,4) [note: 'Метрика recall (макро-усредненная)']
      f1_score decimal(5,4) [note: 'Метрика F1-score (макро-усредненная)']
      training_duration_seconds integer [note: 'Длительность обучения в секундах']
      is_active boolean [not null, default: true, note: 'Флаг активности модели']
      trained_at timestamp [not null, default: `now()`, note: 'Дата и время последнего обучения']
      created_at timestamp [not null, default: `now()`]
      updated_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id [unique]
      }
    }

    Table model_training_history {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      model_id uuid [ref: > user_classifier_models.id, note: 'Связь с моделью']
      training_type varchar(50) [not null, default: 'full', note: 'Тип обучения: full, incremental, retrain']
      samples_count integer [not null, note: 'Количество примеров в обучающей выборке']
      categories_count integer [not null, note: 'Количество категорий в обучающей выборке']
      duration_seconds integer [not null, note: 'Длительность обучения в секундах']
      status varchar(20) [not null, default: 'pending', note: 'Статус: pending, running, completed, failed']
      error_message text [note: 'Сообщение об ошибке (если статус failed)']
      metrics jsonb [note: 'Метрики обучения (accuracy, precision, recall, f1 и т.д.)']
      triggered_by varchar(50) [not null, default: 'manual', note: 'Источник запуска: manual, scheduler, feedback_threshold, periodic']
      started_at timestamp [not null, default: `now()`, note: 'Дата и время начала обучения']
      completed_at timestamp [note: 'Дата и время завершения обучения']
      created_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        model_id
        status
        started_at [note: 'DESC']
      }
    }

    Table feedback_events {
      id uuid [primary key]
      user_id uuid [not null, ref: > users.id, note: 'Идентификатор пользователя']
      transaction_id uuid [not null, ref: > transactions.id, note: 'Идентификатор транзакции']
      predicted_category_id uuid [ref: > categories.id, note: 'Предсказанная категория']
      correct_category_id uuid [not null, ref: > categories.id, note: 'Правильная категория (введенная пользователем)']
      prediction_confidence decimal(5,4) [note: 'Уверенность модели в предсказании на момент события']
      feedback_type varchar(50) [not null, default: 'correction', note: 'Тип обратной связи: correction, confirmation, rejection']
      is_used_for_training boolean [not null, default: true, note: 'Флаг использования в обучении']
      created_at timestamp [not null, default: `now()`]
      
      indexes {
        user_id
        transaction_id
        created_at [note: 'DESC']
      }
    }
    ```

---

Ссылка на интерактивную [ERD диаграмму](https://dbdiagram.io/d/moneycluster-global-69091b7a6735e111700d01cf)

**Основная схема**
![ERD Global](../data/images/moneycluster_erd_global.svg)


Полная схема:
![ERD Global Full](../data/images/moneycluster_erd_global_full.svg)

## **System Architecture (UML)**

### Component Diagram

```plantuml
@startuml
!theme plain
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF

package "Frontend Layer" {
  component [Web Application] as Web
  component [Mobile App] as Mobile
}

package "API Layer" {
  package "FastAPI Gateway" {
    component [Receipt Upload Endpoint] as ReceiptUpload
    component [Transaction Endpoint] as TransEndpoint
    component [Account Endpoint] as AccountEndpoint
    component [Category Endpoint] as CategoryEndpoint
    component [Predict Endpoint] as PredictEndpoint
    component [Feedback Endpoint] as FeedbackEndpoint
  }
  component [FastAPI Gateway] as API
}

package "Business Logic Layer" {
  component [Receipt Service] as ReceiptService
  component [OCR Service] as OCRService
  component [Transaction Service] as TransService
  component [Transaction Group Service] as TransGroupService
  component [Account Service] as AccountService
  component [Category Service] as CatService
  component [Store Service] as StoreService
  component [Tag Service] as TagService
  component [Model Service] as ModelService
  component [Feedback Loop Service] as FeedbackService
}

package "ML Services Layer" {
  component [Embedding Service] as Embedding
  note right of Embedding : Общая модель эмбеддингов\n(sentence-transformers)\nall-MiniLM-L6-v2
  component [User Classifier Service] as Classifier
  note right of Classifier : Персональный классификатор\n(scikit-learn)\nдля каждого пользователя
  component [Training Scheduler] as Scheduler
}

package "Data Layer" {
  database "PostgreSQL" as DB
  storage "Model Storage (S3/Local)" as ModelStorage
  storage "File Storage (S3/Local)" as FileStorage
}

' Frontend connections
Web --> API : HTTPS/REST
Mobile --> API : HTTPS/REST

' API to Business Logic
ReceiptUpload --> ReceiptService
TransEndpoint --> TransService
AccountEndpoint --> AccountService
CategoryEndpoint --> CatService
PredictEndpoint --> ModelService
FeedbackEndpoint --> FeedbackService

' Business Logic connections
ReceiptService --> OCRService : process_receipt(file)
ReceiptService --> StoreService : identify_store(data)
ReceiptService --> TransGroupService : create_group(receipt_data)
TransService --> TransGroupService : group_transactions()
TransService --> AccountService : update_balance()
AccountService --> TransService : get_account_transactions()
TransService --> TagService : manage_tags()
ModelService --> Embedding : get_embedding(text)
ModelService --> Classifier : predict(embedding)
ModelService --> Classifier : train(user_data)
FeedbackService --> ModelService : trigger_retraining()
Scheduler --> ModelService : periodic_retraining()

' Business Logic to Data Layer
ReceiptService --> DB : CRUD receipts
ReceiptService --> FileStorage : save receipt files
OCRService --> DB : update receipt OCR data
TransService --> DB : CRUD transactions
TransGroupService --> DB : CRUD transaction_groups
AccountService --> DB : CRUD accounts, update balance
CatService --> DB : CRUD categories
StoreService --> DB : CRUD stores
TagService --> DB : CRUD tags, transaction_tags
ModelService --> DB : read training_data
ModelService --> ModelStorage : save/load models
FeedbackService --> DB : save feedback_events

' ML Services to Data Layer
Classifier --> Embedding : use embeddings
Classifier --> ModelStorage : load/save model
Classifier --> DB : read training_data

@enduml
```

### Sequence Diagram: Receipt Upload and Processing Flow

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

actor User
participant "Web App" as Web
participant "API Gateway" as API
participant "Receipt Service" as ReceiptSvc
participant "OCR Service" as OCRSvc
participant "Store Service" as StoreSvc
participant "Transaction Group Service" as TransGroupSvc
participant "Model Service" as ModelSvc
participant "Transaction Service" as TransSvc
participant "Database" as DB
participant "File Storage" as FileStorage

== Upload Receipt ==
User -> Web: Upload receipt image
Web -> API: POST /receipts/upload
activate API
API -> ReceiptSvc: save_receipt_file(user_id, file)
activate ReceiptSvc
ReceiptSvc -> FileStorage: save file
activate FileStorage
FileStorage --> ReceiptSvc: file_path
deactivate FileStorage
ReceiptSvc -> DB: INSERT receipt (status: pending)
activate DB
DB --> ReceiptSvc: receipt_id
deactivate DB
deactivate ReceiptSvc
API --> Web: {receipt_id, status: "uploaded"}
deactivate API
Web --> User: Receipt uploaded

== Process Receipt (Background) ==
ReceiptSvc -> OCRSvc: process_receipt(receipt_id, file_path)
activate OCRSvc
OCRSvc -> FileStorage: read file
activate FileStorage
FileStorage --> OCRSvc: file_data
deactivate FileStorage
OCRSvc -> OCRSvc: extract_text (OCR)
OCRSvc -> OCRSvc: parse_receipt_data
OCRSvc --> ReceiptSvc: {text, items, total_amount, date, store_name}
deactivate OCRSvc

ReceiptSvc -> StoreSvc: identify_or_create_store(user_id, store_name)
activate StoreSvc
StoreSvc -> DB: find_store_by_name(user_id, store_name)
activate DB
alt Store exists
  DB --> StoreSvc: store_id
else Store not found
  StoreSvc -> DB: INSERT store
  DB --> StoreSvc: new_store_id
end
deactivate DB
StoreSvc --> ReceiptSvc: store_id
deactivate StoreSvc

ReceiptSvc -> DB: UPDATE receipt (ocr_text, extracted_data, store_id, status: processing)
activate DB
DB --> ReceiptSvc: updated
deactivate DB

ReceiptSvc -> TransGroupSvc: create_transaction_group(user_id, receipt_id, store_id, items)
activate TransGroupSvc
TransGroupSvc -> DB: INSERT transaction_group
activate DB
DB --> TransGroupSvc: group_id
deactivate DB

loop For each item in receipt
  TransGroupSvc -> ModelSvc: predict_category(user_id, item.description)
  activate ModelSvc
  ModelSvc -> ModelSvc: get_embedding(item.description)
  ModelSvc -> ModelSvc: predict_category(embedding)
  ModelSvc --> TransGroupSvc: {predicted_category_id, confidence}
  deactivate ModelSvc
  
  TransGroupSvc -> TransSvc: create_transaction(group_id, item, predicted_category_id)
  activate TransSvc
  TransSvc -> DB: INSERT transaction
  activate DB
  DB --> TransSvc: transaction_id
  deactivate DB
  deactivate TransSvc
end

TransGroupSvc -> DB: UPDATE transaction_group (total_amount)
activate DB
DB --> TransGroupSvc: updated
deactivate DB
deactivate TransGroupSvc

ReceiptSvc -> DB: UPDATE receipt (status: completed)
activate DB
DB --> ReceiptSvc: updated
deactivate DB
deactivate ReceiptSvc

@enduml
```

### Sequence Diagram: Manual Transaction Creation with Category Prediction

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

actor User
participant "Web App" as Web
participant "API Gateway" as API
participant "Transaction Service" as TransSvc
participant "Account Service" as AccountSvc
participant "Model Service" as ModelSvc
participant "Embedding Service" as Embedding
participant "User Classifier" as Classifier
participant "Database" as DB
participant "Model Storage" as Storage

== Create Transaction ==
User -> Web: Create transaction (description, amount, account)
Web -> API: POST /transactions
activate API
API -> TransSvc: create_transaction(user_id, account_id, description, amount)
activate TransSvc

TransSvc -> ModelSvc: predict_category(user_id, description)
activate ModelSvc

ModelSvc -> Embedding: get_embedding(description)
activate Embedding
Embedding --> ModelSvc: embedding_vector[384]
deactivate Embedding

ModelSvc -> Storage: load_user_model(user_id)
activate Storage
alt Model exists
  Storage --> ModelSvc: user_classifier_model
  ModelSvc -> Classifier: predict(embedding, model)
  activate Classifier
  Classifier --> ModelSvc: {category_id, confidence}
  deactivate Classifier
else No model yet
  ModelSvc --> TransSvc: null
end
deactivate Storage
deactivate ModelSvc

TransSvc -> DB: INSERT transaction (predicted_category_id)
activate DB
DB --> TransSvc: transaction_id
deactivate DB

TransSvc -> AccountSvc: update_account_balance(account_id)
activate AccountSvc
AccountSvc -> DB: UPDATE account balance
activate DB
DB --> AccountSvc: updated
deactivate DB
deactivate AccountSvc

deactivate TransSvc
API --> Web: {transaction_id, predicted_category_id, confidence}
deactivate API
Web --> User: Transaction created with predicted category

@enduml
```

### Sequence Diagram: User Feedback and Model Retraining

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

actor User
participant "Web App" as Web
participant "API Gateway" as API
participant "Feedback Service" as FeedbackSvc
participant "Transaction Service" as TransSvc
participant "Model Service" as ModelSvc
participant "Embedding Service" as Embedding
participant "User Classifier" as Classifier
participant "Database" as DB
participant "Model Storage" as Storage

== User Corrects Category ==
User -> Web: Correct category for transaction
Web -> API: POST /feedback {transaction_id, correct_category_id}
activate API
API -> FeedbackSvc: save_feedback(transaction_id, correct_category_id)
activate FeedbackSvc

FeedbackSvc -> TransSvc: get_transaction(transaction_id)
activate TransSvc
TransSvc -> DB: SELECT transaction
activate DB
DB --> TransSvc: transaction data
deactivate DB
deactivate TransSvc

FeedbackSvc -> DB: UPDATE transaction (category_id = correct_category_id)
activate DB
DB --> FeedbackSvc: updated
deactivate DB

FeedbackSvc -> Embedding: get_embedding(transaction.description)
activate Embedding
Embedding --> FeedbackSvc: embedding_vector[384]
deactivate Embedding

FeedbackSvc -> DB: INSERT training_data(embedding, correct_category_id)
activate DB
DB --> FeedbackSvc: training_data_id
deactivate DB

FeedbackSvc -> DB: INSERT feedback_event(transaction_id, predicted_category_id, correct_category_id)
activate DB
DB --> FeedbackSvc: feedback_id
deactivate DB

FeedbackSvc -> ModelSvc: trigger_retraining(user_id)
activate ModelSvc
ModelSvc -> DB: INSERT training_history (status: pending)
activate DB
DB --> ModelSvc: history_id
deactivate DB

ModelSvc -> DB: get_all_training_data(user_id)
activate DB
DB --> ModelSvc: training_dataset
deactivate DB

ModelSvc -> DB: UPDATE training_history (status: running)
activate DB
DB --> ModelSvc: updated
deactivate DB

ModelSvc -> Classifier: train(dataset)
activate Classifier
Classifier --> ModelSvc: trained_model, metrics
deactivate Classifier

ModelSvc -> Storage: save_model(user_id, model)
activate Storage
Storage --> ModelSvc: saved
deactivate Storage

ModelSvc -> DB: UPDATE user_classifier_model (accuracy, metrics, trained_at)
activate DB
DB --> ModelSvc: updated
deactivate DB

ModelSvc -> DB: UPDATE training_history (status: completed, metrics, duration)
activate DB
DB --> ModelSvc: updated
deactivate DB

deactivate ModelSvc
deactivate FeedbackSvc
API --> Web: {status: "feedback_saved", "retraining_completed"}
deactivate API
Web --> User: Category updated, model retrained

@enduml
```

### Sequence Diagram: Get Account Balance

```plantuml
@startuml
!theme plain
skinparam backgroundColor #FFFFFF

actor User
participant "Web App" as Web
participant "API Gateway" as API
participant "Account Service" as AccountSvc
participant "Transaction Service" as TransSvc
participant "Database" as DB

== Get Account Balance ==
User -> Web: View account balance
Web -> API: GET /accounts/{account_id}/balance
activate API
API -> AccountSvc: get_account_balance(account_id)
activate AccountSvc

AccountSvc -> DB: SELECT account (balance)
activate DB
alt Balance is cached and fresh
  DB --> AccountSvc: balance
else Balance needs recalculation
  AccountSvc -> TransSvc: calculate_balance_from_transactions(account_id)
  activate TransSvc
  TransSvc -> DB: SELECT SUM(amount) WHERE account_id = X AND type = 'income'
  activate DB
  DB --> TransSvc: total_income
  deactivate DB
  TransSvc -> DB: SELECT SUM(amount) WHERE account_id = X AND type = 'expense'
  activate DB
  DB --> TransSvc: total_expense
  deactivate DB
  TransSvc -> TransSvc: balance = total_income - total_expense
  TransSvc --> AccountSvc: calculated_balance
  AccountSvc -> DB: UPDATE account (balance = calculated_balance)
  activate DB
  DB --> AccountSvc: updated
  deactivate DB
  deactivate TransSvc
end
deactivate DB

AccountSvc --> API: balance
deactivate AccountSvc
API --> Web: {account_id, balance, currency}
deactivate API
Web --> User: Display account balance

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
  + get_accounts(): List[Account]
  + get_transactions(): List[Transaction]
  + get_categories(): List[Category]
  + get_receipts(): List[Receipt]
  + get_model(): UserClassifierModel
}

class Account {
  - id: UUID
  - user_id: UUID
  - parent_account_id: UUID
  - name: String
  - balance: Decimal
  - currency: String
  + get_balance(): Decimal
  + get_transactions(): List[Transaction]
  + get_children(): List[Account]
}

class Category {
  - id: UUID
  - user_id: UUID
  - parent_id: UUID
  - name: String
  - type: Enum
  + get_transactions(): List[Transaction]
  + get_children(): List[Category]
}

class Transaction {
  - id: UUID
  - account_id: UUID
  - transaction_group_id: UUID
  - type: Enum
  - amount: Decimal
  - description: String
  - category_id: UUID
  - predicted_category_id: UUID
  - comment: String
  + predict_category(): Category
  + update_category(category_id: UUID): void
  + add_tag(tag_id: UUID): void
  + to_training_sample(): TrainingData
}

class TransactionGroup {
  - id: UUID
  - user_id: UUID
  - receipt_id: UUID
  - store_id: UUID
  - total_amount: Decimal
  + get_transactions(): List[Transaction]
  + get_receipt(): Receipt
}

class Receipt {
  - id: UUID
  - user_id: UUID
  - store_id: UUID
  - file_path: String
  - ocr_text: String
  - extracted_data: JSON
  - processing_status: String
  + process(): void
  + get_transaction_group(): TransactionGroup
}

class Store {
  - id: UUID
  - user_id: UUID
  - name: String
  - address: String
  + get_receipts(): List[Receipt]
}

class Tag {
  - id: UUID
  - user_id: UUID
  - name: String
  - color: String
}

class TransactionTag {
  - transaction_id: UUID
  - tag_id: UUID
}

class TrainingData {
  - id: UUID
  - user_id: UUID
  - transaction_id: UUID
  - embedding: Vector[384]
  - category_id: UUID
  - source: String
}

class UserClassifierModel {
  - user_id: UUID
  - model_type: String
  - model_path: String
  - accuracy: Float
  - trained_at: DateTime
  + predict(embedding: Vector): Tuple[Category, Float]
  + train(dataset: List[TrainingData]): void
}

class EmbeddingModel {
  - model_name: String
  - dimension: Int = 384
  + encode(text: String): Vector[384]
  + encode_batch(texts: List[String]): List[Vector[384]]
}

class FeedbackEvent {
  - id: UUID
  - transaction_id: UUID
  - predicted_category_id: UUID
  - correct_category_id: UUID
  - feedback_type: String
}

' Relationships
User "1" *-- "many" Account : has
User "1" *-- "many" Category : defines
User "1" *-- "many" Receipt : has
User "1" *-- "many" Store : has
User "1" *-- "many" Tag : has
User "1" -- "1" UserClassifierModel : owns

Account "1" *-- "many" Account : parent-child
Account "1" *-- "many" Transaction : has

Category "1" *-- "many" Category : parent-child
Category "1" *-- "many" Transaction : categorizes
Category "1" *-- "many" Transaction : predicted_for

TransactionGroup "1" *-- "many" Transaction : contains
TransactionGroup "1" -- "1" Receipt : created_from

Receipt "1" -- "1" Store : from
Receipt "1" -- "1" TransactionGroup : generates

Transaction "many" *-- "many" Tag : tagged_with

Transaction "1" -- "0..1" TrainingData : converts to
UserClassifierModel "1" *-- "many" TrainingData : trained on
UserClassifierModel ..> EmbeddingModel : uses

Transaction "1" *-- "many" FeedbackEvent : has

note right of UserClassifierModel
  Персональный классификатор
  для каждого пользователя.
  Использует общий EmbeddingModel.
end note

note right of TransactionGroup
  Группа транзакций из одного чека.
  Один чек может содержать
  несколько позиций.
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

node "Processing Services" {
  [OCR Service\n(Multiple Instances)] as OCRSvc1
  [OCR Service\n(Multiple Instances)] as OCRSvc2
  [Receipt Processing Queue] as ReceiptQueue
}

node "Database Server" {
  database "PostgreSQL" as PG {
    [User Data]
    [Account Data]
    [Transaction Data]
    [Category Data]
    [Receipt Data]
    [Store Data]
    [Tag Data]
    [Training Data]
    [Model Metadata]
  }
}

node "Storage Cluster" {
  storage "Model Storage\n(S3/Local FS)" as ModelStorage {
    [User Models\n(joblib/pickle)]
  }
  storage "File Storage\n(S3/Local FS)" as FileStorage {
    [Receipt Images]
    [Receipt PDFs]
  }
}

node "Background Workers" {
  [Training Scheduler] as TrainScheduler
  [Receipt Processor] as ReceiptProcessor
  [Retraining Queue] as TrainQueue
}

Browser --> CDN : HTTPS
MobileApp --> CDN : HTTPS
CDN --> WebApp : HTTP
WebApp --> FastAPI : REST API

FastAPI --> EmbedSvc : gRPC / HTTP
FastAPI --> ClassifierSvc1 : gRPC / HTTP
FastAPI --> ClassifierSvc2 : gRPC / HTTP
FastAPI --> PG : SQL
FastAPI --> ReceiptQueue : Queue receipt processing

ReceiptQueue --> OCRSvc1 : OCR tasks
ReceiptQueue --> OCRSvc2 : OCR tasks
OCRSvc1 --> FileStorage : Read receipt files
OCRSvc2 --> FileStorage : Read receipt files

ClassifierSvc1 --> ModelStorage : Read/Write models
ClassifierSvc2 --> ModelStorage : Read/Write models

TrainScheduler --> FastAPI : Trigger retraining
TrainScheduler --> TrainQueue : Queue training jobs
TrainQueue --> ClassifierSvc1 : Training tasks
TrainQueue --> ClassifierSvc2 : Training tasks

ReceiptProcessor --> ReceiptQueue : Process receipts
ReceiptProcessor --> FastAPI : Update receipt status

note right of EmbedSvc
  Общая модель эмбеддингов
  для всех пользователей
end note

note right of ClassifierSvc1
  Персональные классификаторы
  масштабируются горизонтально
end note

note right of OCRSvc1
  OCR сервисы для обработки
  чеков в фоновом режиме
end note

@enduml
```

