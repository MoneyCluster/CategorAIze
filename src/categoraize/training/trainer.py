"""Модуль для обучения модели."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from categoraize.data.loader import DataLoader
from categoraize.data.preprocessor import DataPreprocessor
from categoraize.models.classifier import ProductCategoryClassifier

logger = logging.getLogger(__name__)


class Trainer:
    """Класс для обучения модели классификации."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Инициализация тренера.

        Args:
            config: Словарь с конфигурацией обучения
        """
        self.config = config
        self.model: ProductCategoryClassifier | None = None
        self.preprocessor: DataPreprocessor | None = None
        self.id_to_label: dict[int, str] | None = None

        logger.info("Инициализирован Trainer")

    def load_data(self) -> pd.DataFrame:
        """
        Загрузка данных из конфигурации.

        Returns:
            Загруженный DataFrame
        """
        data_config = self.config["data"]
        data_path = Path(data_config["path"])
        filename = data_config.get("filename", "product_titles.csv")
        column_mapping = data_config.get("column_mapping", None)

        loader = DataLoader(data_path)
        df = loader.load_kaggle_dataset(filename, column_mapping=column_mapping)

        # Валидация данных
        loader.validate_data(df)

        return df

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Предобработка данных.

        Args:
            df: Исходный DataFrame

        Returns:
            Обработанный DataFrame
        """
        preprocessor_config = self.config.get("preprocessing", {})
        self.preprocessor = DataPreprocessor(
            lowercase=preprocessor_config.get("lowercase", True),
            remove_punctuation=preprocessor_config.get("remove_punctuation", False),
        )

        df_processed = self.preprocessor.preprocess_dataframe(df)
        return df_processed

    def split_data(self, df: pd.DataFrame) -> tuple:
        """
        Разделение данных на train/validation/test.

        Args:
            df: DataFrame с данными

        Returns:
            Tuple (X_train, X_val, X_test, y_train, y_val, y_test, id_to_label)
        """
        split_config = self.config.get("split", {})
        test_size = split_config.get("test_size", 0.2)
        val_size = split_config.get("val_size", 0.1)
        random_seed = split_config.get("random_seed", 42)

        # Проверка, можно ли использовать stratify (все классы должны иметь минимум 2 примера)
        category_counts = df["category"].value_counts()
        can_stratify = (category_counts >= 2).all()

        # Разделение на train и временный test
        split_kwargs = {
            "test_size": test_size,
            "random_state": random_seed,
        }
        if can_stratify:
            split_kwargs["stratify"] = df["category"]

        X_temp, X_test, y_temp, y_test = train_test_split(
            df["product_title"],
            df["category"],
            **split_kwargs,
        )

        # Проверка, можно ли использовать stratify для train/val разделения
        temp_category_counts = y_temp.value_counts()
        n_classes = len(temp_category_counts)

        # Для stratify нужно:
        # 1. Каждый класс должен иметь минимум 2 примера в train
        # 2. Размер validation set должен быть >= количеству классов
        val_size_adjusted = val_size / (1 - test_size)
        n_val_samples = int(len(y_temp) * val_size_adjusted)

        can_stratify_val = (
            n_classes > 1
            and (temp_category_counts >= 2).all()
            and n_val_samples >= n_classes
            and len(y_temp) - n_val_samples >= n_classes
        )

        # Разделение train на train и validation
        val_split_kwargs = {
            "test_size": val_size_adjusted,
            "random_state": random_seed,
        }
        if can_stratify_val:
            val_split_kwargs["stratify"] = y_temp

        X_train, X_val, y_train, y_val = train_test_split(
            X_temp,
            y_temp,
            **val_split_kwargs,
        )

        # Кодирование меток
        _, self.id_to_label = self.preprocessor.encode_labels(df["category"])

        logger.info("Разделение данных:")
        logger.info(f"  Train: {len(X_train)} примеров")
        logger.info(f"  Validation: {len(X_val)} примеров")
        logger.info(f"  Test: {len(X_test)} примеров")

        return (
            X_train.tolist(),
            X_val.tolist(),
            X_test.tolist(),
            y_train.tolist(),
            y_val.tolist(),
            y_test.tolist(),
            self.id_to_label,
        )

    def create_model(self) -> ProductCategoryClassifier:
        """
        Создание модели согласно конфигурации.

        Returns:
            Инициализированная модель
        """
        model_config = self.config["model"]

        self.model = ProductCategoryClassifier(
            embedding_model_name=model_config.get(
                "embedding_model_name", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            classifier_type=model_config.get("classifier_type", "mlp"),
            classifier_params=model_config.get("classifier_params", {}),
        )

        logger.info("Модель создана")
        return self.model

    def train(
        self,
        X_train: list[str],
        y_train: list[str],
        use_class_weights: bool = True,
    ) -> ProductCategoryClassifier:
        """
        Обучение модели.

        Args:
            X_train: Список названий продуктов для обучения
            y_train: Список категорий для обучения
            use_class_weights: Использовать ли веса классов

        Returns:
            Обученная модель
        """
        if self.model is None:
            raise ValueError("Модель не создана. Вызовите create_model()")

        logger.info("Начало обучения модели...")

        class_weights = None
        if use_class_weights:
            # Вычисление весов классов
            y_train_series = pd.Series(y_train)
            encoded_labels, id_to_label = self.preprocessor.encode_labels(y_train_series)
            class_weights = self.preprocessor.get_class_weights(encoded_labels)

        self.model.fit(X_train, y_train, class_weights=class_weights)

        logger.info("Обучение завершено")

        return self.model

    def save_model(self, save_path: str | Path) -> None:
        """
        Сохранение обученной модели.

        Args:
            save_path: Путь для сохранения
        """
        if self.model is None:
            raise ValueError("Модель не обучена")

        save_path = Path(save_path)
        logger.info(f"Сохранение модели в {save_path}")
        self.model.save_pretrained(save_path)

    def run_training(self) -> tuple:
        """
        Запуск полного пайплайна обучения.

        Returns:
            Tuple (обученная модель, данные для валидации)
        """
        logger.info("=" * 60)
        logger.info("Начало пайплайна обучения")
        logger.info("=" * 60)

        # 1. Загрузка данных
        logger.info("Шаг 1: Загрузка данных")
        df = self.load_data()

        # 2. Предобработка
        logger.info("Шаг 2: Предобработка данных")
        df_processed = self.preprocess_data(df)

        # 3. Разделение данных
        logger.info("Шаг 3: Разделение данных")
        X_train, X_val, X_test, y_train, y_val, y_test, id_to_label = self.split_data(df_processed)

        # 4. Создание модели
        logger.info("Шаг 4: Создание модели")
        model = self.create_model()

        # 5. Обучение
        logger.info("Шаг 5: Обучение модели")
        model = self.train(X_train, y_train)

        # 6. Сохранение модели
        save_path = Path(self.config.get("output", {}).get("model_path", "models/checkpoint"))
        logger.info("Шаг 6: Сохранение модели")
        self.save_model(save_path)

        logger.info("=" * 60)
        logger.info("Пайплайн обучения завершен успешно")
        logger.info("=" * 60)

        # Возврат данных для валидации
        validation_data = {
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
            "id_to_label": id_to_label,
        }

        return model, validation_data
