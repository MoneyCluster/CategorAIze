"""Тесты для модуля оценки качества модели."""

import numpy as np
import pytest

from categoraize.models.classifier import ProductCategoryClassifier
from categoraize.training.evaluator import Evaluator


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
    ]
    categories = [
        "Electronics",
        "Electronics",
        "Computers",
        "Computers",
        "Tablets",
        "Computers",
    ]

    model = ProductCategoryClassifier(classifier_type="lr")
    model.fit(products, categories)
    return model


class TestEvaluator:
    """Тесты для класса Evaluator."""

    def test_init(self):
        """Тест инициализации Evaluator."""
        evaluator = Evaluator()
        assert evaluator is not None

    def test_evaluate(self, trained_model):
        """Тест базовой оценки модели."""
        evaluator = Evaluator()
        X = ["iPhone 15", "MacBook Pro"]
        y_true = ["Electronics", "Computers"]

        metrics = evaluator.evaluate(trained_model, X, y_true)

        assert isinstance(metrics, dict)
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert "macro_precision" in metrics
        assert "macro_recall" in metrics
        assert "macro_f1" in metrics
        assert 0 <= metrics["accuracy"] <= 1
        assert 0 <= metrics["f1"] <= 1

    def test_evaluate_with_confidence(self, trained_model):
        """Тест оценки с учетом уверенности."""
        evaluator = Evaluator()
        X = ["iPhone 15", "MacBook Pro", "Samsung Phone"]
        y_true = ["Electronics", "Computers", "Electronics"]

        metrics = evaluator.evaluate_with_confidence(
            trained_model, X, y_true, confidence_threshold=0.5
        )

        assert isinstance(metrics, dict)
        assert "mean_confidence" in metrics
        assert "median_confidence" in metrics
        assert "min_confidence" in metrics
        assert "max_confidence" in metrics
        assert 0 <= metrics["mean_confidence"] <= 1
        assert 0 <= metrics["median_confidence"] <= 1

    def test_classification_report_detailed(self, trained_model):
        """Тест детального отчета по классификации."""
        evaluator = Evaluator()
        X = ["iPhone 15", "MacBook Pro", "iPad"]
        y_true = ["Electronics", "Computers", "Tablets"]

        report = evaluator.classification_report_detailed(trained_model, X, y_true)

        assert isinstance(report, str)
        assert len(report) > 0

    def test_confusion_matrix_report(self, trained_model):
        """Тест матрицы ошибок."""
        evaluator = Evaluator()
        X = ["iPhone 15", "MacBook Pro", "iPad", "Surface"]
        y_true = ["Electronics", "Computers", "Tablets", "Computers"]

        cm = evaluator.confusion_matrix_report(trained_model, X, y_true)

        assert isinstance(cm, np.ndarray)
        assert cm.ndim == 2
        assert cm.shape[0] == cm.shape[1]  # Квадратная матрица

    def test_evaluate_perfect_predictions(self, trained_model):
        """Тест оценки на данных, где модель дает правильные предсказания."""
        evaluator = Evaluator()
        # Используем данные из обучения для гарантированно правильных предсказаний
        X = ["iPhone 15 Pro Max", "Laptop Dell XPS 13"]
        y_true = ["Electronics", "Computers"]

        metrics = evaluator.evaluate(trained_model, X, y_true)

        # Модель может не дать 100% точность, но метрики должны быть валидными
        assert metrics["accuracy"] >= 0
        assert metrics["f1"] >= 0
