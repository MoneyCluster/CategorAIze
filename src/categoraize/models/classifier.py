"""Модуль для модели классификации продуктов по категориям."""

import logging
from pathlib import Path

import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

logger = logging.getLogger(__name__)


class ProductCategoryClassifier:
    """
    Модель классификации продуктов по категориям.

    Использует общий эмбеддер для продуктов и категорий,
    затем легкий классификатор для финального предсказания.
    """

    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        classifier_type: str = "mlp",
        classifier_params: dict | None = None,
    ) -> None:
        """
        Инициализация модели.

        Args:
            embedding_model_name: Название модели для эмбеддингов
            classifier_type: Тип классификатора ('lr' или 'mlp')
            classifier_params: Параметры классификатора
        """
        self.embedding_model_name = embedding_model_name
        self.classifier_type = classifier_type
        self.classifier_params = classifier_params or {}

        # Инициализация эмбеддера
        logger.info(f"Загрузка эмбеддера: {embedding_model_name}")
        self.embedder = SentenceTransformer(embedding_model_name)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        logger.info(f"Размерность эмбеддингов: {self.embedding_dim}")

        # Инициализация классификатора
        if classifier_type == "lr":
            # Убираем max_iter из дефолтных параметров, если он уже есть в classifier_params
            default_params = {"max_iter": 1000, "random_state": 42}
            default_params.update(self.classifier_params)
            self.classifier: BaseEstimator = LogisticRegression(**default_params)
        elif classifier_type == "mlp":
            default_params = {
                "hidden_layer_sizes": (128, 64),
                "max_iter": 500,
                "random_state": 42,
                "early_stopping": True,
                "validation_fraction": 0.1,
            }
            default_params.update(self.classifier_params)
            self.classifier = MLPClassifier(**default_params)
        else:
            raise ValueError(f"Неизвестный тип классификатора: {classifier_type}")

        logger.info(f"Инициализирован классификатор типа: {classifier_type}")

        # Метаданные
        self.id_to_label: dict[int, str] | None = None
        self.label_to_id: dict[str, int] | None = None
        self.is_fitted = False

    def encode_products(self, products: list[str]) -> np.ndarray:
        """
        Получение эмбеддингов для продуктов.

        Args:
            products: Список названий продуктов

        Returns:
            Массив эмбеддингов формы (n_products, embedding_dim)
        """
        logger.debug(f"Кодирование {len(products)} продуктов")
        embeddings = self.embedder.encode(products, show_progress_bar=False)
        return np.array(embeddings)

    def encode_categories(self, categories: list[str]) -> np.ndarray:
        """
        Получение эмбеддингов для категорий.

        Args:
            categories: Список названий категорий

        Returns:
            Массив эмбеддингов формы (n_categories, embedding_dim)
        """
        logger.debug(f"Кодирование {len(categories)} категорий")
        embeddings = self.embedder.encode(categories, show_progress_bar=False)
        return np.array(embeddings)

    def fit(
        self,
        product_titles: list[str],
        categories: list[str],
        class_weights: np.ndarray | None = None,
    ) -> "ProductCategoryClassifier":
        """
        Обучение модели.

        Args:
            product_titles: Список названий продуктов
            categories: Список категорий (строками)
            class_weights: Веса классов (опционально)

        Returns:
            self
        """
        logger.info(f"Начало обучения на {len(product_titles)} примерах")

        # Создание mapping для категорий
        unique_categories = sorted(set(categories))
        self.label_to_id = {label: idx for idx, label in enumerate(unique_categories)}
        self.id_to_label = {idx: label for label, idx in self.label_to_id.items()}

        logger.info(f"Количество категорий: {len(unique_categories)}")

        # Кодирование категорий в числовые метки
        y_data = np.array([self.label_to_id[cat] for cat in categories])

        # Получение эмбеддингов для продуктов
        x_data = self.encode_products(product_titles)

        logger.info(f"Форма данных для обучения: X={x_data.shape}, y={y_data.shape}")

        # Обучение классификатора
        if class_weights is not None and hasattr(self.classifier, "class_weight"):
            # Для LogisticRegression
            class_weight_dict = dict(enumerate(class_weights))
            self.classifier.set_params(class_weight=class_weight_dict)

        logger.info("Обучение классификатора...")
        self.classifier.fit(x_data, y_data)

        self.is_fitted = True
        logger.info("Обучение завершено успешно")

        return self

    def predict(self, product_titles: list[str]) -> list[str]:
        """
        Предсказание категорий для списка продуктов.

        Args:
            product_titles: Список названий продуктов

        Returns:
            Список предсказанных категорий
        """
        if not self.is_fitted:
            raise ValueError("Модель не обучена. Вызовите fit() перед predict()")

        # Обработка пустого списка
        if len(product_titles) == 0:
            return []

        logger.debug(f"Предсказание для {len(product_titles)} продуктов")

        # Получение эмбеддингов
        x_data = self.encode_products(product_titles)

        # Предсказание
        y_pred = self.classifier.predict(x_data)

        # Преобразование обратно в категории
        categories = [self.id_to_label[int(pred)] for pred in y_pred]

        return categories

    def predict_proba(self, product_titles: list[str]) -> np.ndarray:
        """
        Предсказание вероятностей для каждого класса.

        Args:
            product_titles: Список названий продуктов

        Returns:
            Массив вероятностей формы (n_products, n_classes)
        """
        if not self.is_fitted:
            raise ValueError("Модель не обучена. Вызовите fit() перед predict_proba()")

        # Обработка пустого списка
        if len(product_titles) == 0:
            return np.array([]).reshape(0, len(self.id_to_label))

        logger.debug(f"Предсказание вероятностей для {len(product_titles)} продуктов")

        # Получение эмбеддингов
        x_data = self.encode_products(product_titles)

        # Предсказание вероятностей
        probabilities = self.classifier.predict_proba(x_data)

        return probabilities

    def predict_with_confidence(self, product_titles: list[str]) -> tuple[list[str], np.ndarray]:
        """
        Предсказание категорий с уровнями уверенности.

        Args:
            product_titles: Список названий продуктов

        Returns:
            Tuple (предсказанные категории, уровни уверенности)
        """
        # Обработка пустого списка
        if len(product_titles) == 0:
            return [], np.array([])

        probabilities = self.predict_proba(product_titles)
        confidences = np.max(probabilities, axis=1)
        predictions = self.predict(product_titles)

        return predictions, confidences

    def save_pretrained(self, save_path: str | Path) -> None:
        """
        Сохранение модели в формате, совместимом с Hugging Face.

        Args:
            save_path: Путь для сохранения модели
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Сохранение модели в {save_path}")

        # Сохранение эмбеддера
        embedder_path = save_path / "embedder"
        self.embedder.save(str(embedder_path))

        # Сохранение классификатора
        classifier_path = save_path / "classifier.joblib"
        joblib.dump(self.classifier, classifier_path)

        # Сохранение метаданных
        import json

        metadata = {
            "embedding_model_name": self.embedding_model_name,
            "classifier_type": self.classifier_type,
            "classifier_params": self.classifier_params,
            "embedding_dim": self.embedding_dim,
            "id_to_label": self.id_to_label,
            "label_to_id": self.label_to_id,
            "is_fitted": self.is_fitted,
        }

        metadata_path = save_path / "metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info("Модель успешно сохранена")

    @classmethod
    def from_pretrained(cls, load_path: str | Path) -> "ProductCategoryClassifier":
        """
        Загрузка модели из сохраненного состояния.

        Args:
            load_path: Путь к сохраненной модели

        Returns:
            Загруженная модель
        """
        load_path = Path(load_path)

        logger.info(f"Загрузка модели из {load_path}")

        # Загрузка метаданных
        import json

        metadata_path = load_path / "metadata.json"
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)

        # Создание экземпляра модели
        model = cls(
            embedding_model_name=metadata["embedding_model_name"],
            classifier_type=metadata["classifier_type"],
            classifier_params=metadata["classifier_params"],
        )

        # Загрузка классификатора
        classifier_path = load_path / "classifier.joblib"
        model.classifier = joblib.load(classifier_path)

        # Загрузка метаданных
        model.id_to_label = {int(k): v for k, v in metadata["id_to_label"].items()}
        model.label_to_id = {v: int(k) for k, v in metadata["id_to_label"].items()}
        model.is_fitted = metadata["is_fitted"]

        logger.info("Модель успешно загружена")

        return model
