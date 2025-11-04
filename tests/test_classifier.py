"""Тесты для модуля классификатора."""

import numpy as np
import pytest

from categoraize.models.classifier import ProductCategoryClassifier


@pytest.fixture
def sample_data():
    """Создание тестовых данных."""
    products = [
        "iPhone 15 Pro Max",
        "Samsung Galaxy S24",
        "Laptop Dell XPS 13",
        "MacBook Pro M3",
        "iPad Air",
        "Surface Pro",
    ]
    categories = [
        "Electronics",
        "Electronics",
        "Computers",
        "Computers",
        "Tablets",
        "Computers",
    ]
    return products, categories


class TestProductCategoryClassifier:
    """Тесты для класса ProductCategoryClassifier."""

    def test_init_default(self):
        """Тест инициализации с параметрами по умолчанию."""
        model = ProductCategoryClassifier()
        assert model.embedding_model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert model.classifier_type == "mlp"
        assert model.is_fitted is False

    def test_init_custom(self):
        """Тест инициализации с кастомными параметрами."""
        model = ProductCategoryClassifier(
            embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
            classifier_type="lr",
            classifier_params={"max_iter": 500},
        )
        assert model.classifier_type == "lr"
        assert model.is_fitted is False

    def test_init_invalid_classifier_type(self):
        """Тест инициализации с неверным типом классификатора."""
        with pytest.raises(ValueError, match="Неизвестный тип классификатора"):
            ProductCategoryClassifier(classifier_type="invalid")

    def test_encode_products(self, sample_data):
        """Тест кодирования продуктов."""
        products, _ = sample_data
        model = ProductCategoryClassifier()

        embeddings = model.encode_products(products[:3])

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3
        assert embeddings.shape[1] == model.embedding_dim

    def test_encode_categories(self):
        """Тест кодирования категорий."""
        categories = ["Electronics", "Computers", "Tablets"]
        model = ProductCategoryClassifier()

        embeddings = model.encode_categories(categories)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3
        assert embeddings.shape[1] == model.embedding_dim

    def test_fit(self, sample_data):
        """Тест обучения модели."""
        products, categories = sample_data
        model = ProductCategoryClassifier(classifier_type="lr")

        model.fit(products, categories)

        assert model.is_fitted is True
        assert model.id_to_label is not None
        assert model.label_to_id is not None
        assert len(model.id_to_label) == len(set(categories))

    def test_predict_not_fitted(self):
        """Тест предсказания без обучения."""
        model = ProductCategoryClassifier()
        with pytest.raises(ValueError, match="Модель не обучена"):
            model.predict(["Product 1"])

    def test_predict(self, sample_data):
        """Тест предсказания категорий."""
        products, categories = sample_data
        model = ProductCategoryClassifier(classifier_type="lr")
        model.fit(products, categories)

        predictions = model.predict(products[:2])

        assert isinstance(predictions, list)
        assert len(predictions) == 2
        assert all(isinstance(p, str) for p in predictions)
        assert all(p in categories for p in predictions)

    def test_predict_proba(self, sample_data):
        """Тест предсказания вероятностей."""
        products, categories = sample_data
        model = ProductCategoryClassifier(classifier_type="lr")
        model.fit(products, categories)

        probabilities = model.predict_proba(products[:2])

        assert isinstance(probabilities, np.ndarray)
        assert probabilities.shape[0] == 2
        assert probabilities.shape[1] == len(set(categories))
        # Проверка, что вероятности суммируются в 1
        assert np.allclose(probabilities.sum(axis=1), 1.0)

    def test_predict_with_confidence(self, sample_data):
        """Тест предсказания с уверенностью."""
        products, categories = sample_data
        model = ProductCategoryClassifier(classifier_type="lr")
        model.fit(products, categories)

        predictions, confidences = model.predict_with_confidence(products[:2])

        assert isinstance(predictions, list)
        assert isinstance(confidences, np.ndarray)
        assert len(predictions) == 2
        assert len(confidences) == 2
        assert all(0 <= c <= 1 for c in confidences)

    def test_save_and_load(self, sample_data, tmp_path):
        """Тест сохранения и загрузки модели."""
        products, categories = sample_data
        model = ProductCategoryClassifier(classifier_type="lr")
        model.fit(products, categories)

        # Сохранение
        save_path = tmp_path / "test_model"
        model.save_pretrained(save_path)

        # Проверка наличия файлов
        assert (save_path / "embedder").exists()
        assert (save_path / "classifier.joblib").exists()
        assert (save_path / "metadata.json").exists()

        # Загрузка
        loaded_model = ProductCategoryClassifier.from_pretrained(save_path)

        assert loaded_model.is_fitted is True
        assert loaded_model.id_to_label == model.id_to_label
        assert loaded_model.label_to_id == model.label_to_id

        # Проверка, что предсказания совпадают
        test_products = ["iPhone 15", "MacBook"]
        original_preds = model.predict(test_products)
        loaded_preds = loaded_model.predict(test_products)

        assert original_preds == loaded_preds
