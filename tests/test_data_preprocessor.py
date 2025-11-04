"""Тесты для модуля предобработки данных."""

import numpy as np
import pandas as pd
import pytest

from categoraize.data.preprocessor import DataPreprocessor


@pytest.fixture
def sample_data():
    """Создание тестового датасета."""
    return pd.DataFrame(
        {
            "product_title": [
                "iPhone 15 Pro Max",
                "Samsung Galaxy S24",
                "  Laptop Dell XPS 13  ",
                "MacBook Pro M3",
                "Product with   multiple   spaces",
            ],
            "category": ["Electronics", "Electronics", "Computers", "Computers", "Other"],
        }
    )


class TestDataPreprocessor:
    """Тесты для класса DataPreprocessor."""

    def test_init_default(self):
        """Тест инициализации с параметрами по умолчанию."""
        preprocessor = DataPreprocessor()
        assert preprocessor.lowercase is True
        assert preprocessor.remove_punctuation is False

    def test_init_custom(self):
        """Тест инициализации с кастомными параметрами."""
        preprocessor = DataPreprocessor(lowercase=False, remove_punctuation=True)
        assert preprocessor.lowercase is False
        assert preprocessor.remove_punctuation is True

    def test_preprocess_text_lowercase(self):
        """Тест предобработки текста с приведением к нижнему регистру."""
        preprocessor = DataPreprocessor(lowercase=True)
        result = preprocessor.preprocess_text("iPhone 15 Pro Max")
        assert result == "iphone 15 pro max"

    def test_preprocess_text_no_lowercase(self):
        """Тест предобработки текста без приведения к нижнему регистру."""
        preprocessor = DataPreprocessor(lowercase=False)
        result = preprocessor.preprocess_text("iPhone 15 Pro Max")
        assert result == "iPhone 15 Pro Max"

    def test_preprocess_text_remove_punctuation(self):
        """Тест предобработки текста с удалением пунктуации."""
        preprocessor = DataPreprocessor(lowercase=False, remove_punctuation=True)
        result = preprocessor.preprocess_text("Product, with! punctuation?")
        assert result == "Product with punctuation"

    def test_preprocess_text_whitespace(self):
        """Тест предобработки текста с множественными пробелами."""
        preprocessor = DataPreprocessor()
        result = preprocessor.preprocess_text("Product   with    spaces")
        assert result == "product with spaces"

    def test_preprocess_text_empty(self):
        """Тест предобработки пустого текста."""
        preprocessor = DataPreprocessor()
        result = preprocessor.preprocess_text("")
        assert result == ""

    def test_preprocess_text_nan(self):
        """Тест предобработки NaN значения."""
        preprocessor = DataPreprocessor()
        result = preprocessor.preprocess_text(pd.NA)
        assert result == ""

    def test_preprocess_dataframe(self, sample_data):
        """Тест предобработки DataFrame."""
        preprocessor = DataPreprocessor(lowercase=True)
        result = preprocessor.preprocess_dataframe(sample_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)
        assert result["product_title"].iloc[0] == "iphone 15 pro max"
        assert result["product_title"].iloc[2] == "laptop dell xps 13"
        assert result["product_title"].iloc[4] == "product with multiple spaces"

    def test_preprocess_dataframe_removes_empty(self):
        """Тест удаления пустых строк после предобработки."""
        df = pd.DataFrame(
            {
                "product_title": ["Product 1", "   ", "Product 3"],
                "category": ["A", "B", "C"],
            }
        )
        preprocessor = DataPreprocessor()
        result = preprocessor.preprocess_dataframe(df)

        assert len(result) == 2
        assert "product 1" in result["product_title"].values  # lowercase применяется
        assert "product 3" in result["product_title"].values

    def test_encode_labels(self):
        """Тест кодирования меток."""
        preprocessor = DataPreprocessor()
        labels = pd.Series(["Category A", "Category B", "Category A", "Category C"])

        encoded, id_to_label = preprocessor.encode_labels(labels)

        assert isinstance(encoded, pd.Series)
        assert len(encoded) == len(labels)
        assert encoded.unique().tolist() == [0, 1, 2]
        assert isinstance(id_to_label, dict)
        assert len(id_to_label) == 3
        assert id_to_label[0] == "Category A"
        assert id_to_label[1] == "Category B"
        assert id_to_label[2] == "Category C"

    def test_encode_labels_consistency(self):
        """Тест консистентности кодирования меток."""
        preprocessor = DataPreprocessor()
        labels = pd.Series(["A", "B", "A", "C"])

        encoded1, id_to_label1 = preprocessor.encode_labels(labels)
        encoded2, id_to_label2 = preprocessor.encode_labels(labels)

        # Проверка консистентности
        assert (encoded1 == encoded2).all()
        assert id_to_label1 == id_to_label2

    def test_get_class_weights(self):
        """Тест вычисления весов классов."""
        preprocessor = DataPreprocessor()
        encoded_labels = pd.Series([0, 0, 0, 1, 1, 2])  # Несбалансированные данные

        weights = preprocessor.get_class_weights(encoded_labels)

        assert isinstance(weights, np.ndarray)
        assert len(weights) == 3
        # Класс 0 встречается чаще, должен иметь меньший вес
        assert weights[0] < weights[1]
        assert weights[0] < weights[2]

    def test_get_class_weights_balanced(self):
        """Тест вычисления весов для сбалансированных данных."""
        preprocessor = DataPreprocessor()
        encoded_labels = pd.Series([0, 0, 1, 1, 2, 2])  # Сбалансированные данные

        weights = preprocessor.get_class_weights(encoded_labels)

        # Все веса должны быть одинаковыми для сбалансированных данных
        assert np.allclose(weights, weights[0])
