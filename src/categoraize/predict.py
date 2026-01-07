"""Скрипт для офлайн-инференса модели."""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from categoraize.models.classifier import ProductCategoryClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Главная функция для выполнения предсказаний."""
    parser = argparse.ArgumentParser(description="Офлайн-инференс модели классификации продуктов")
    parser.add_argument(
        "--input_path",
        type=str,
        required=True,
        help="Путь к входному CSV файлу с данными для предсказания",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Путь к выходному CSV файлу с результатами предсказаний",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default="models/checkpoint",
        help="Путь к сохраненной модели",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Запуск офлайн-инференса")
    logger.info("=" * 60)

    # 1. Загрузка модели
    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Модель не найдена: {model_path}")

    logger.info(f"Загрузка модели из {model_path}")
    model = ProductCategoryClassifier.from_pretrained(model_path)
    logger.info("Модель успешно загружена")

    # 2. Загрузка данных
    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Входной файл не найден: {input_path}")

    logger.info(f"Загрузка данных из {input_path}")
    df = pd.read_csv(input_path)

    # Проверка наличия колонки product_title
    if "product_title" not in df.columns:
        raise ValueError(
            f"Входной файл должен содержать колонку 'product_title'. "
            f"Найдены колонки: {list(df.columns)}"
        )

    product_titles = df["product_title"].tolist()
    logger.info(f"Загружено {len(product_titles)} записей для предсказания")

    # 3. Выполнение предсказаний
    logger.info("Выполнение предсказаний...")
    predictions, confidences = model.predict_with_confidence(product_titles)
    logger.info("Предсказания выполнены")

    # 4. Сохранение результатов
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results_df = pd.DataFrame(
        {
            "product_title": product_titles,
            "predicted_category": predictions,
            "confidence": confidences,
        }
    )

    results_df.to_csv(output_path, index=False)
    logger.info(f"Результаты сохранены в {output_path}")

    # Статистика предсказаний
    logger.info("=" * 60)
    logger.info("Статистика предсказаний:")
    logger.info(f"  Всего записей: {len(results_df)}")
    logger.info(f"  Средняя уверенность: {confidences.mean():.4f}")
    logger.info(f"  Минимальная уверенность: {confidences.min():.4f}")
    logger.info(f"  Максимальная уверенность: {confidences.max():.4f}")
    logger.info(f"  Уникальных категорий: {results_df['predicted_category'].nunique()}")
    logger.info("=" * 60)
    logger.info("Офлайн-инференс завершен успешно")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

