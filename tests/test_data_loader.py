"""Тесты для модуля загрузки данных."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from categoraize.data.loader import DataLoader


@pytest.fixture
def sample_data():
    """Создание тестового датасета."""
    return pd.DataFrame(
        {
            "product_title": [
                "iPhone 15 Pro Max",
                "Samsung Galaxy S24",
                "Laptop Dell XPS 13",
                "MacBook Pro M3",
            ],
            "category": ["Electronics", "Electronics", "Computers", "Computers"],
        }
    )


@pytest.fixture
def sample_data_alternative_columns():
    """Создание тестового датасета с альтернативными названиями колонок."""
    return pd.DataFrame(
        {
            "title": [
                "iPhone 15 Pro Max",
                "Samsung Galaxy S24",
                "Laptop Dell XPS 13",
                "MacBook Pro M3",
            ],
            "category_name": ["Electronics", "Electronics", "Computers", "Computers"],
        }
    )


@pytest.fixture
def temp_data_dir(sample_data):
    """Создание временной директории с тестовыми данными."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "product_titles.csv"
        sample_data.to_csv(data_path, index=False)
        yield tmpdir


class TestDataLoader:
    """Тесты для класса DataLoader."""

    def test_init(self):
        """Тест инициализации DataLoader."""
        loader = DataLoader("data")
        assert loader.data_path == Path("data")

    def test_load_kaggle_dataset(self, temp_data_dir):
        """Тест загрузки данных из CSV файла."""
        loader = DataLoader(temp_data_dir)
        df = loader.load_kaggle_dataset("product_titles.csv")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert "product_title" in df.columns
        assert "category" in df.columns

    def test_load_kaggle_dataset_missing_file(self):
        """Тест обработки отсутствующего файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DataLoader(tmpdir)
            with pytest.raises(FileNotFoundError):
                loader.load_kaggle_dataset("nonexistent.csv")

    def test_load_kaggle_dataset_missing_columns(self, temp_data_dir):
        """Тест обработки отсутствующих колонок."""
        # Создаем файл с неправильными колонками, которые не могут быть автодетектированы
        wrong_data = pd.DataFrame({"col1": ["Product 1"], "col2": ["Category 1"]})
        wrong_path = Path(temp_data_dir) / "wrong.csv"
        wrong_data.to_csv(wrong_path, index=False)

        loader = DataLoader(temp_data_dir)
        with pytest.raises(ValueError, match="отсутствуют необходимые колонки"):
            loader.load_kaggle_dataset("wrong.csv")

    def test_load_kaggle_dataset_autodetect_columns(self, temp_data_dir, sample_data_alternative_columns):
        """Тест автодетекта колонок с альтернативными названиями."""
        # Создаем файл с альтернативными названиями колонок
        data_path = Path(temp_data_dir) / "alternative.csv"
        sample_data_alternative_columns.to_csv(data_path, index=False)

        loader = DataLoader(temp_data_dir)
        df = loader.load_kaggle_dataset("alternative.csv")

        # Проверяем, что колонки переименованы в стандартные
        assert "product_title" in df.columns
        assert "category" in df.columns
        assert len(df) == 4
        assert df["product_title"].iloc[0] == "iPhone 15 Pro Max"

    def test_load_kaggle_dataset_custom_mapping(self, temp_data_dir, sample_data_alternative_columns):
        """Тест загрузки с кастомным маппингом колонок."""
        # Создаем файл с альтернативными названиями колонок
        data_path = Path(temp_data_dir) / "custom.csv"
        sample_data_alternative_columns.to_csv(data_path, index=False)

        loader = DataLoader(temp_data_dir)
        column_mapping = {"product_title": "title", "category": "category_name"}
        df = loader.load_kaggle_dataset("custom.csv", column_mapping=column_mapping)

        # Проверяем, что колонки переименованы правильно
        assert "product_title" in df.columns
        assert "category" in df.columns
        assert len(df) == 4

    def test_validate_data_success(self, sample_data):
        """Тест успешной валидации данных."""
        loader = DataLoader("data")
        result = loader.validate_data(sample_data)
        assert result is True

    def test_validate_data_empty(self):
        """Тест валидации пустого датасета."""
        loader = DataLoader("data")
        empty_df = pd.DataFrame({"product_title": [], "category": []})
        with pytest.raises(ValueError, match="Датасет пуст"):
            loader.validate_data(empty_df)

    def test_validate_data_missing_columns(self):
        """Тест валидации данных с отсутствующими колонками."""
        loader = DataLoader("data")
        wrong_df = pd.DataFrame({"title": ["Product 1"]})
        with pytest.raises(ValueError, match="Отсутствуют необходимые колонки"):
            loader.validate_data(wrong_df)

    def test_validate_data_wrong_types(self):
        """Тест валидации данных с неправильными типами."""
        loader = DataLoader("data")
        wrong_df = pd.DataFrame({"product_title": [1, 2, 3], "category": ["A", "B", "C"]})
        with pytest.raises(ValueError, match="должна быть строкового типа"):
            loader.validate_data(wrong_df)

    def test_validate_data_missing_values(self):
        """Тест валидации данных с пропусками."""
        loader = DataLoader("data")
        df_with_nulls = pd.DataFrame(
            {
                "product_title": ["Product 1", None, "Product 3"],
                "category": ["A", "B", None],
            }
        )
        with pytest.raises(ValueError, match="пропуски"):
            loader.validate_data(df_with_nulls)

    def test_validate_data_empty_strings(self):
        """Тест валидации данных с пустыми строками."""
        loader = DataLoader("data")
        df_empty = pd.DataFrame(
            {"product_title": ["Product 1", "", "Product 3"], "category": ["A", "B", "C"]}
        )
        with pytest.raises(ValueError, match="пустых названий"):
            loader.validate_data(df_empty)

    def test_validate_data_insufficient_categories(self):
        """Тест валидации данных с недостаточным количеством категорий."""
        loader = DataLoader("data")
        df_single_cat = pd.DataFrame(
            {
                "product_title": ["Product 1", "Product 2"],
                "category": ["A", "A"],
            }
        )
        with pytest.raises(ValueError, match="Недостаточно категорий"):
            loader.validate_data(df_single_cat)
