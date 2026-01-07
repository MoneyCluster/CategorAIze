"""Скрипт для стадии evaluate DVC пайплайна: оценка качества модели."""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Добавляем путь к src для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from categoraize.models.classifier import ProductCategoryClassifier
from categoraize.training.evaluator import Evaluator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Главная функция для оценки модели."""
    parser = argparse.ArgumentParser(description="Оценка качества модели")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Путь к сохраненной модели",
    )
    parser.add_argument(
        "--val-data",
        type=str,
        default="data/processed/val.csv",
        help="Путь к валидационным данным",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default="data/processed/test.csv",
        help="Путь к тестовым данным",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="metrics",
        help="Директория для сохранения метрик",
    )

    args = parser.parse_args()

    # Создание выходной директории
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Стадия evaluate: Оценка качества модели")
    logger.info("=" * 60)

    # 1. Загрузка модели
    logger.info(f"Загрузка модели из {args.model_path}")
    model = ProductCategoryClassifier.from_pretrained(args.model_path)

    # 2. Загрузка данных
    logger.info(f"Загрузка валидационных данных из {args.val_data}")
    val_df = pd.read_csv(args.val_data)
    X_val = val_df["product_title"].tolist()
    y_val = val_df["category"].tolist()

    logger.info(f"Загрузка тестовых данных из {args.test_data}")
    test_df = pd.read_csv(args.test_data)
    X_test = test_df["product_title"].tolist()
    y_test = test_df["category"].tolist()

    # 3. Оценка модели
    evaluator = Evaluator()

    logger.info("\nОценка на Validation set:")
    val_metrics = evaluator.evaluate_with_confidence(model, X_val, y_val)

    logger.info("\nОценка на Test set:")
    test_metrics = evaluator.evaluate_with_confidence(model, X_test, y_test)

    # 4. Сохранение метрик
    logger.info(f"Сохранение метрик в {output_dir}")

    val_metrics_dict = {
        "accuracy": float(val_metrics["accuracy"]),
        "macro_f1": float(val_metrics["macro_f1"]),
        "weighted_f1": float(val_metrics["weighted_f1"]),
        "mean_confidence": float(val_metrics["mean_confidence"]),
    }

    test_metrics_dict = {
        "accuracy": float(test_metrics["accuracy"]),
        "macro_f1": float(test_metrics["macro_f1"]),
        "weighted_f1": float(test_metrics["weighted_f1"]),
        "mean_confidence": float(test_metrics["mean_confidence"]),
    }

    with (output_dir / "val_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(val_metrics_dict, f, indent=2, ensure_ascii=False)

    with (output_dir / "test_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(test_metrics_dict, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info("Стадия evaluate завершена успешно")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

