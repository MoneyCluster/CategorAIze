"""Скрипт для стадии prepare DVC пайплайна: загрузка и предобработка данных."""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# Добавляем путь к src для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from categoraize.data.loader import DataLoader
from categoraize.data.preprocessor import DataPreprocessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Главная функция для подготовки данных."""
    parser = argparse.ArgumentParser(description="Подготовка данных для обучения")
    parser.add_argument(
        "--input",
        type=str,
        default="data/product_titles.csv",
        help="Путь к входному CSV файлу",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Директория для сохранения обработанных данных",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Доля тестовой выборки",
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=0.1,
        help="Доля валидационной выборки (от train)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Seed для воспроизводимости",
    )
    parser.add_argument(
        "--lowercase",
        action="store_true",
        default=True,
        help="Приводить текст к нижнему регистру",
    )
    parser.add_argument(
        "--remove-punctuation",
        action="store_true",
        help="Удалять пунктуацию",
    )

    args = parser.parse_args()

    # Создание выходной директории
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Стадия prepare: Загрузка и предобработка данных")
    logger.info("=" * 60)

    # 1. Загрузка данных
    logger.info(f"Загрузка данных из {args.input}")
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Файл данных не найден: {input_path}")

    loader = DataLoader(input_path.parent)
    df = loader.load_kaggle_dataset(input_path.name)
    loader.validate_data(df)

    # 2. Предобработка
    logger.info("Предобработка данных...")
    preprocessor = DataPreprocessor(
        lowercase=args.lowercase,
        remove_punctuation=args.remove_punctuation,
    )
    df_processed = preprocessor.preprocess_dataframe(df)

    # 3. Разделение данных
    logger.info("Разделение данных на train/val/test...")
    test_size = args.test_size
    val_size = args.val_size
    random_seed = args.random_seed

    # Проверка возможности использования stratify
    category_counts = df_processed["category"].value_counts()
    can_stratify = (category_counts >= 2).all()

    # Разделение на train и test
    split_kwargs = {
        "test_size": test_size,
        "random_state": random_seed,
    }
    if can_stratify:
        split_kwargs["stratify"] = df_processed["category"]

    X_temp, X_test, y_temp, y_test = train_test_split(
        df_processed["product_title"],
        df_processed["category"],
        **split_kwargs,
    )

    # Разделение train на train и val
    temp_category_counts = y_temp.value_counts()
    n_classes = len(temp_category_counts)
    val_size_adjusted = val_size / (1 - test_size)
    n_val_samples = int(len(y_temp) * val_size_adjusted)

    can_stratify_val = (
        n_classes > 1
        and (temp_category_counts >= 2).all()
        and n_val_samples >= n_classes
        and len(y_temp) - n_val_samples >= n_classes
    )

    val_split_kwargs = {
        "test_size": val_size_adjusted,
        "random_state": random_seed,
    }
    if can_stratify_val:
        val_split_kwargs["stratify"] = y_temp

    X_train, X_val, y_train, y_val = train_test_split(
        X_temp,
        y_temp,
        **val_split_kwargs,
    )

    logger.info(f"Train: {len(X_train)} примеров")
    logger.info(f"Validation: {len(X_val)} примеров")
    logger.info(f"Test: {len(X_test)} примеров")

    # 4. Сохранение данных
    logger.info(f"Сохранение данных в {output_dir}")

    train_df = pd.DataFrame({"product_title": X_train, "category": y_train})
    val_df = pd.DataFrame({"product_title": X_val, "category": y_val})
    test_df = pd.DataFrame({"product_title": X_test, "category": y_test})

    train_df.to_csv(output_dir / "train.csv", index=False)
    val_df.to_csv(output_dir / "val.csv", index=False)
    test_df.to_csv(output_dir / "test.csv", index=False)

    logger.info("=" * 60)
    logger.info("Стадия prepare завершена успешно")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

