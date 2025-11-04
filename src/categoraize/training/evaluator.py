"""Модуль для оценки качества модели."""

import logging
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)


class Evaluator:
    """Класс для оценки качества модели."""

    def __init__(self) -> None:
        """Инициализация оценщика."""
        logger.info("Инициализирован Evaluator")

    def evaluate(
        self,
        model: Any,
        X: list[str],
        y_true: list[str],
        average: str = "weighted",
    ) -> dict[str, float]:
        """
        Оценка модели на данных.

        Args:
            model: Обученная модель
            X: Список названий продуктов
            y_true: Истинные категории
            average: Метод усреднения для метрик ('micro', 'macro', 'weighted')

        Returns:
            Словарь с метриками
        """
        logger.info(f"Оценка модели на {len(X)} примерах")

        # Предсказания
        y_pred = model.predict(X)

        # Базовые метрики
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average=average, zero_division=0)
        recall = recall_score(y_true, y_pred, average=average, zero_division=0)
        f1 = f1_score(y_true, y_pred, average=average, zero_division=0)

        # Macro метрики
        macro_precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
        macro_recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
        macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "macro_precision": float(macro_precision),
            "macro_recall": float(macro_recall),
            "macro_f1": float(macro_f1),
        }

        logger.info("Метрики:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  Precision ({average}): {precision:.4f}")
        logger.info(f"  Recall ({average}): {recall:.4f}")
        logger.info(f"  F1-score ({average}): {f1:.4f}")
        logger.info(f"  Macro F1: {macro_f1:.4f}")

        return metrics

    def evaluate_with_confidence(
        self,
        model: Any,
        X: list[str],
        y_true: list[str],
        confidence_threshold: float = 0.5,
    ) -> dict[str, Any]:
        """
        Оценка модели с учетом уверенности предсказаний.

        Args:
            model: Обученная модель
            X: Список названий продуктов
            y_true: Истинные категории
            confidence_threshold: Порог уверенности

        Returns:
            Словарь с метриками и статистикой уверенности
        """
        logger.info(f"Оценка модели с учетом уверенности на {len(X)} примерах")

        # Предсказания с уверенностью
        y_pred, confidences = model.predict_with_confidence(X)

        # Базовые метрики на всех данных
        metrics = self.evaluate(model, X, y_true)

        # Метрики на данных с высокой уверенностью
        high_confidence_mask = confidences >= confidence_threshold
        n_high_confidence = high_confidence_mask.sum()

        if n_high_confidence > 0:
            X_high = [X[i] for i in range(len(X)) if high_confidence_mask[i]]
            y_true_high = [y_true[i] for i in range(len(y_true)) if high_confidence_mask[i]]
            y_pred_high = [y_pred[i] for i in range(len(y_pred)) if high_confidence_mask[i]]

            high_conf_accuracy = accuracy_score(y_true_high, y_pred_high)

            metrics["high_confidence_accuracy"] = float(high_conf_accuracy)
            metrics["high_confidence_count"] = int(n_high_confidence)
            metrics["high_confidence_ratio"] = float(n_high_confidence / len(X))

            logger.info(
                f"Точность на данных с уверенностью >= {confidence_threshold}: {high_conf_accuracy:.4f}"
            )
            logger.info(
                f"Количество таких примеров: {n_high_confidence} ({n_high_confidence/len(X)*100:.1f}%)"
            )

        # Статистика уверенности
        metrics["mean_confidence"] = float(np.mean(confidences))
        metrics["median_confidence"] = float(np.median(confidences))
        metrics["min_confidence"] = float(np.min(confidences))
        metrics["max_confidence"] = float(np.max(confidences))

        logger.info(f"Средняя уверенность: {metrics['mean_confidence']:.4f}")
        logger.info(f"Медианная уверенность: {metrics['median_confidence']:.4f}")

        return metrics

    def classification_report_detailed(
        self,
        model: Any,
        X: list[str],
        y_true: list[str],
        id_to_label: dict[int, str] | None = None,
    ) -> str:
        """
        Детальный отчет по классификации.

        Args:
            model: Обученная модель
            X: Список названий продуктов
            y_true: Истинные категории
            id_to_label: Mapping для меток (опционально, не используется)

        Returns:
            Строка с отчетом
        """
        y_pred = model.predict(X)

        report: str = classification_report(y_true, y_pred, zero_division=0)
        logger.info("\n" + "=" * 60)
        logger.info("Детальный отчет по классификации:")
        logger.info("=" * 60)
        logger.info("\n" + report)

        return report

    def confusion_matrix_report(
        self,
        model: Any,
        X: list[str],
        y_true: list[str],
    ) -> np.ndarray:
        """
        Получение матрицы ошибок.

        Args:
            model: Обученная модель
            X: Список названий продуктов
            y_true: Истинные категории

        Returns:
            Матрица ошибок
        """
        y_pred = model.predict(X)
        cm: np.ndarray = confusion_matrix(y_true, y_pred)

        logger.info("Матрица ошибок:")
        logger.info(f"\n{cm}")

        return cm
