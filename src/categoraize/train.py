"""Скрипт для запуска обучения модели."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from categoraize.training.evaluator import Evaluator
from categoraize.training.trainer import Trainer


def setup_logging(verbose: bool = False) -> None:
    """
    Настройка логирования.

    Args:
        verbose: Включить ли детальное логирование
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(config_path: str | Path) -> dict[str, Any]:
    """
    Загрузка конфигурации из YAML файла.

    Args:
        config_path: Путь к конфигурационному файлу

    Returns:
        Словарь с конфигурацией
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def main() -> None:
    """Главная функция для запуска обучения."""
    parser = argparse.ArgumentParser(description="Обучение модели классификации продуктов")
    parser.add_argument(
        "config",
        type=str,
        help="Путь к конфигурационному файлу (YAML)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Включить детальное логирование",
    )

    args = parser.parse_args()

    # Настройка логирования
    setup_logging(verbose=args.verbose)

    logger = logging.getLogger(__name__)

    try:
        # Загрузка конфигурации
        logger.info(f"Загрузка конфигурации из {args.config}")
        config = load_config(args.config)

        # Создание тренера
        trainer = Trainer(config)

        # Запуск обучения
        model, validation_data = trainer.run_training()

        # Оценка модели
        logger.info("=" * 60)
        logger.info("Оценка качества модели")
        logger.info("=" * 60)

        evaluator = Evaluator()

        # Оценка на validation set
        logger.info("\nОценка на Validation set:")
        val_metrics = evaluator.evaluate_with_confidence(
            model,
            validation_data["X_val"],
            validation_data["y_val"],
        )

        # Оценка на test set
        logger.info("\nОценка на Test set:")
        test_metrics = evaluator.evaluate_with_confidence(
            model,
            validation_data["X_test"],
            validation_data["y_test"],
        )

        # Детальный отчет
        logger.info("\nДетальный отчет по Test set:")
        evaluator.classification_report_detailed(
            model,
            validation_data["X_test"],
            validation_data["y_test"],
        )

        logger.info("=" * 60)
        logger.info("Обучение и оценка завершены успешно")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Ошибка при обучении: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
