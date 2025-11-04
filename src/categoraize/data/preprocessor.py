"""Модуль для предобработки данных."""

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Класс для предобработки текстовых данных."""

    def __init__(self, lowercase: bool = True, remove_punctuation: bool = False) -> None:
        """
        Инициализация препроцессора.

        Args:
            lowercase: Приводить ли текст к нижнему регистру
            remove_punctuation: Удалять ли пунктуацию
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        logger.info(
            f"Инициализирован DataPreprocessor: lowercase={lowercase}, "
            f"remove_punctuation={remove_punctuation}"
        )

    def preprocess_text(self, text: str) -> str:
        """
        Предобработка одного текста.

        Args:
            text: Исходный текст

        Returns:
            Обработанный текст
        """
        if pd.isna(text) or text == "":
            return ""

        # Приведение к строке на случай не-строковых значений
        text = str(text).strip()

        if self.lowercase:
            text = text.lower()

        if self.remove_punctuation:
            # Удаление пунктуации, оставляем только буквы, цифры и пробелы
            text = re.sub(r"[^\w\s]", "", text)

        # Удаление множественных пробелов
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Предобработка DataFrame с текстовыми данными.

        Args:
            df: DataFrame с колонкой 'product_title'

        Returns:
            DataFrame с обработанными данными
        """
        logger.info("Начало предобработки данных...")

        df = df.copy()

        # Предобработка названий продуктов
        if "product_title" in df.columns:
            df["product_title"] = df["product_title"].apply(self.preprocess_text)
            logger.info("Предобработка названий продуктов завершена")

        # Предобработка категорий (только нормализация)
        if "category" in df.columns:
            df["category"] = df["category"].str.strip()
            logger.info("Предобработка категорий завершена")

        # Удаление пустых строк после предобработки
        initial_len = len(df)
        df = df[df["product_title"].str.len() > 0].reset_index(drop=True)
        removed = initial_len - len(df)

        if removed > 0:
            logger.warning(f"Удалено {removed} записей с пустыми названиями после предобработки")

        logger.info(f"Предобработка завершена. Осталось {len(df)} записей")
        return df

    def encode_labels(self, labels: pd.Series) -> tuple[pd.Series, dict]:
        """
        Кодирование категорий в числовые метки.

        Args:
            labels: Серия с категориями

        Returns:
            Tuple (encoded_labels, id_to_label mapping)
        """
        unique_labels = sorted(labels.unique())
        label_to_id = {label: idx for idx, label in enumerate(unique_labels)}
        id_to_label = {idx: label for label, idx in label_to_id.items()}

        encoded = labels.map(label_to_id)

        logger.info(f"Закодировано {len(unique_labels)} категорий")
        logger.debug(f"Mapping: {label_to_id}")

        return encoded, id_to_label

    def get_class_weights(self, encoded_labels: pd.Series) -> np.ndarray:
        """
        Вычисление весов классов для несбалансированных данных.

        Args:
            encoded_labels: Закодированные метки (числовые)

        Returns:
            Массив весов классов
        """
        class_counts = encoded_labels.value_counts().sort_index()
        total = len(encoded_labels)
        n_classes = len(class_counts)

        # Вычисление весов: обратная пропорциональность частоте
        weights = np.array([total / (n_classes * count) for count in class_counts.values])

        logger.info(f"Вычислены веса классов для {n_classes} категорий")
        logger.debug(f"Веса: {dict(zip(class_counts.index, weights, strict=False))}")

        return weights
