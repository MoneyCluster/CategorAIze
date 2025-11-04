"""Тесты для проверки корректности предсказаний модели (API-уровень)."""

import numpy as np
import pytest

from categoraize.models.classifier import ProductCategoryClassifier


@pytest.fixture
def trained_model():
    """Создание обученной модели для тестов."""
    products = [
        "iPhone 15 Pro Max",
        "Samsung Galaxy S24",
        "Laptop Dell XPS 13",
        "MacBook Pro M3",
        "iPad Air",
        "Surface Pro",
        "Pixel 8",
        "ThinkPad X1",
    ]
    categories = [
        "Electronics",
        "Electronics",
        "Computers",
        "Computers",
        "Tablets",
        "Computers",
        "Electronics",
        "Computers",
    ]

    model = ProductCategoryClassifier(classifier_type="lr")
    model.fit(products, categories)
    return model


class TestPredictions:
    """Тесты для проверки корректности предсказаний."""

    def test_predict_returns_valid_categories(self, trained_model):
        """Тест, что предсказания возвращают валидные категории."""
        test_products = ["New iPhone", "New Laptop"]

        predictions = trained_model.predict(test_products)

        # Проверка, что все предсказания - строки
        assert all(isinstance(p, str) for p in predictions)
        # Проверка, что предсказания находятся в списке категорий модели
        valid_categories = set(trained_model.id_to_label.values())
        assert all(p in valid_categories for p in predictions)

    def test_predict_proba_returns_valid_probabilities(self, trained_model):
        """Тест, что вероятности валидны (сумма = 1, диапазон [0, 1])."""
        test_products = ["New iPhone", "New Laptop"]

        probabilities = trained_model.predict_proba(test_products)

        # Проверка формы
        assert probabilities.shape[0] == len(test_products)
        assert probabilities.shape[1] == len(trained_model.id_to_label)

        # Проверка, что вероятности в диапазоне [0, 1]
        assert np.all(probabilities >= 0)
        assert np.all(probabilities <= 1)

        # Проверка, что сумма вероятностей для каждого примера = 1
        assert np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)

    def test_predict_with_confidence_returns_valid_values(self, trained_model):
        """Тест, что предсказания с уверенностью возвращают валидные значения."""
        test_products = ["New iPhone", "New Laptop"]

        predictions, confidences = trained_model.predict_with_confidence(test_products)

        # Проверка предсказаний
        assert len(predictions) == len(test_products)
        assert all(isinstance(p, str) for p in predictions)

        # Проверка уверенности
        assert len(confidences) == len(test_products)
        assert all(0 <= c <= 1 for c in confidences)
        assert isinstance(confidences, np.ndarray)

    def test_predict_handles_single_product(self, trained_model):
        """Тест обработки одного продукта."""
        prediction = trained_model.predict(["Single Product"])
        assert len(prediction) == 1
        assert isinstance(prediction[0], str)

    def test_predict_handles_empty_list(self, trained_model):
        """Тест обработки пустого списка."""
        predictions = trained_model.predict([])
        assert len(predictions) == 0
        assert isinstance(predictions, list)

    def test_predict_handles_unicode(self, trained_model):
        """Тест обработки Unicode символов."""
        test_products = ["iPhone 15 Pro Макс", "Ноутбук Dell"]

        predictions = trained_model.predict(test_products)

        assert len(predictions) == len(test_products)
        assert all(isinstance(p, str) for p in predictions)

    def test_predict_consistency(self, trained_model):
        """Тест консистентности предсказаний."""
        test_product = "Test Product"

        predictions1 = trained_model.predict([test_product])
        predictions2 = trained_model.predict([test_product])

        # Предсказания должны быть одинаковыми при повторных вызовах
        assert predictions1 == predictions2

    def test_predict_proba_consistency_with_predict(self, trained_model):
        """Тест консистентности между predict и predict_proba."""
        test_products = ["Test Product 1", "Test Product 2"]

        predictions = trained_model.predict(test_products)
        probabilities = trained_model.predict_proba(test_products)

        # Категория с максимальной вероятностью должна совпадать с предсказанием
        predicted_indices = probabilities.argmax(axis=1)
        expected_categories = [trained_model.id_to_label[idx] for idx in predicted_indices]

        assert predictions == expected_categories

    def test_predict_with_confidence_consistency(self, trained_model):
        """Тест консистентности между predict_with_confidence и predict_proba."""
        test_products = ["Test Product 1", "Test Product 2"]

        predictions, confidences = trained_model.predict_with_confidence(test_products)
        probabilities = trained_model.predict_proba(test_products)

        # Уверенность должна совпадать с максимальной вероятностью
        max_probs = probabilities.max(axis=1)
        assert np.allclose(confidences, max_probs, atol=1e-6)

        # Предсказания должны совпадать
        predicted_from_proba = trained_model.predict(test_products)
        assert predictions == predicted_from_proba
