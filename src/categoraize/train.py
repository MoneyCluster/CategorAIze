"""Скрипт для запуска обучения модели."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

try:
    import mlflow
    import mlflow.sklearn
    import mlflow.transformers
except ImportError:
    mlflow = None  # type: ignore[assignment]

from categoraize.training.evaluator import Evaluator
from categoraize.training.trainer import Trainer


def _flatten_config(config: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """
    Преобразование вложенного словаря конфигурации в плоский словарь для MLflow.

    Args:
        config: Вложенный словарь конфигурации
        parent_key: Префикс для ключей
        sep: Разделитель для ключей

    Returns:
        Плоский словарь
    """
    items: list[tuple[str, Any]] = []
    for k, v in config.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, str(v)))
    return dict(items)


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
    if yaml is None:
        raise ImportError("PyYAML не установлен. Установите: pip install pyyaml")

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        loaded: Any = yaml.safe_load(f) if yaml is not None else {}
        config: dict[str, Any] = loaded if isinstance(loaded, dict) else {}

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
        config_path = Path(args.config)

        # Настройка MLflow
        if mlflow is None:
            logger.warning("MLflow не установлен. Трекинг экспериментов отключен.")
            use_mlflow = False
        else:
            use_mlflow = True
            # Включение autolog для sklearn и transformers
            mlflow.sklearn.autolog()
            mlflow.transformers.autolog()

        # Запуск обучения с MLflow трекингом
        from contextlib import nullcontext

        with (mlflow.start_run() if use_mlflow else nullcontext()):
            if use_mlflow:
                # Логирование параметров из конфига
                flat_config = _flatten_config(config)
                mlflow.log_params(flat_config)

                # Логирование конфигурационного файла как артефакта
                mlflow.log_artifact(str(config_path), "config")

                # Логирование dvc.lock если существует
                dvc_lock_path = Path("dvc.lock")
                if dvc_lock_path.exists():
                    mlflow.log_artifact(str(dvc_lock_path), "dvc")
                    logger.info("Логирование dvc.lock в MLflow")

                # Получение хешей DVC для связи данных и эксперимента
                try:
                    import subprocess

                    result = subprocess.run(
                        ["dvc", "dag", "--dot"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        # Попытка получить хеш данных из dvc.lock
                        if dvc_lock_path.exists():
                            import json

                            with dvc_lock_path.open(encoding="utf-8") as f:
                                dvc_lock = yaml.safe_load(f) if yaml else {}
                                # Логируем информацию о версиях данных
                                mlflow.set_tag("dvc_pipeline", "configured")
                except Exception as e:
                    logger.warning(f"Не удалось получить информацию DVC: {e}")

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

            # Логирование метрик в MLflow
            if use_mlflow:
                # Метрики validation set
                mlflow.log_metrics(
                    {
                        "val_accuracy": val_metrics["accuracy"],
                        "val_macro_f1": val_metrics["macro_f1"],
                        "val_weighted_f1": val_metrics["weighted_f1"],
                        "val_mean_confidence": val_metrics["mean_confidence"],
                    }
                )

                # Метрики test set
                mlflow.log_metrics(
                    {
                        "test_accuracy": test_metrics["accuracy"],
                        "test_macro_f1": test_metrics["macro_f1"],
                        "test_weighted_f1": test_metrics["weighted_f1"],
                        "test_mean_confidence": test_metrics["mean_confidence"],
                    }
                )

                # Логирование модели
                model_path = Path(config.get("output", {}).get("model_path", "models/checkpoint"))
                mlflow.sklearn.log_model(
                    model.classifier,  # type: ignore[attr-defined]
                    "classifier",
                    registered_model_name="ProductCategoryClassifier",
                )

                # Логирование пути к модели
                mlflow.log_artifact(str(model_path), "model")

                logger.info(f"MLflow run ID: {mlflow.active_run().info.run_id}")  # type: ignore[attr-defined]

            logger.info("=" * 60)
            logger.info("Обучение и оценка завершены успешно")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Ошибка при обучении: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
