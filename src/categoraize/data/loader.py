"""Модуль для загрузки данных из различных источников."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """Класс для загрузки данных из Kaggle датасета."""

    def __init__(self, data_path: str | Path) -> None:
        """
        Инициализация загрузчика данных.

        Args:
            data_path: Путь к директории с данными или к CSV файлу
        """
        self.data_path = Path(data_path)
        logger.info(f"Инициализирован DataLoader с путем: {self.data_path}")

    def load_kaggle_dataset(
        self, filename: str = "product_titles.csv", column_mapping: dict[str, str] | None = None
    ) -> pd.DataFrame:
        """
        Загрузка датасета из Kaggle (Massive Product Text Classification Dataset).

        Args:
            filename: Имя файла с данными (по умолчанию product_titles.csv)
            column_mapping: Маппинг колонок {стандартное_имя: имя_в_датасете}
                           Если None, будет использован автодетект

        Returns:
            DataFrame с колонками: product_title, category
        """
        file_path = self.data_path / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Файл данных не найден: {file_path}. "
                "Пожалуйста, скачайте датасет с Kaggle и поместите его в директорию data/"
            )

        logger.info(f"Загрузка данных из {file_path}")
        df = pd.read_csv(file_path)

        # Стандартные имена колонок
        standard_columns = {"product_title": "product_title", "category": "category"}

        # Автодетект колонок, если маппинг не указан
        if column_mapping is None:
            column_mapping = {}
            # Возможные варианты названий колонок
            title_variants = ["product_title", "title", "product_name", "name"]
            category_variants = ["category", "category_name", "cat", "label"]

            # Поиск колонки с названием продукта
            for variant in title_variants:
                if variant in df.columns:
                    column_mapping["product_title"] = variant
                    break

            # Поиск колонки с категорией
            for variant in category_variants:
                if variant in df.columns:
                    column_mapping["category"] = variant
                    break

        # Применяем маппинг
        standard_columns.update(column_mapping)

        # Проверка наличия необходимых колонок
        missing_columns = []
        for standard_name, actual_name in standard_columns.items():
            if actual_name not in df.columns:
                missing_columns.append(standard_name)

        if missing_columns:
            raise ValueError(
                f"В датасете отсутствуют необходимые колонки: {missing_columns}. "
                f"Доступные колонки: {list(df.columns)}"
            )

        # Переименовываем колонки в стандартные имена
        df_renamed = df.rename(columns={v: k for k, v in standard_columns.items()})

        # Оставляем только нужные колонки
        df_renamed = df_renamed[["product_title", "category"]].copy()

        logger.info(f"Загружено {len(df_renamed)} записей")
        logger.info(f"Количество категорий: {df_renamed['category'].nunique()}")
        logger.info(f"Распределение категорий:\n{df_renamed['category'].value_counts()}")

        return df_renamed

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Валидация загруженных данных.

        Args:
            df: DataFrame для валидации

        Returns:
            True если данные валидны, иначе выбрасывает исключение

        Raises:
            ValueError: Если данные не соответствуют требованиям
        """
        logger.info("Валидация данных...")

        # Проверка на пустой датасет
        if df.empty:
            raise ValueError("Датасет пуст")

        # Проверка наличия необходимых колонок
        required_columns = ["product_title", "category"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Отсутствуют необходимые колонки: {missing_columns}")

        # Проверка на пропуски (проверяем раньше типов, т.к. пропуски могут влиять на типы)
        missing_values = df[required_columns].isnull().sum()
        if missing_values.any():
            logger.warning(f"Обнаружены пропуски:\n{missing_values}")
            raise ValueError(f"Обнаружены пропуски в данных:\n{missing_values}")

        # Проверка типов данных
        if not pd.api.types.is_string_dtype(df["product_title"]):
            raise ValueError("Колонка 'product_title' должна быть строкового типа")

        if not pd.api.types.is_string_dtype(df["category"]):
            raise ValueError("Колонка 'category' должна быть строкового типа")

        # Проверка на пустые строки
        empty_titles = df["product_title"].str.strip().eq("").sum()
        empty_categories = df["category"].str.strip().eq("").sum()

        if empty_titles > 0:
            raise ValueError(f"Обнаружено {empty_titles} пустых названий продуктов")

        if empty_categories > 0:
            raise ValueError(f"Обнаружено {empty_categories} пустых категорий")

        # Проверка минимального количества категорий
        unique_categories = df["category"].nunique()
        if unique_categories < 2:
            raise ValueError(f"Недостаточно категорий для классификации: {unique_categories}")

        logger.info("Валидация данных успешно пройдена")
        return True
