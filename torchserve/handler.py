"""TorchServe handler для модели классификации продуктов."""

import json
import logging
import os
from pathlib import Path
from typing import Any

import torch

# Добавляем путь к src для импорта модулей
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from categoraize.models.classifier import ProductCategoryClassifier

logger = logging.getLogger(__name__)


class ModelHandler:
    """Обработчик модели для TorchServe."""

    def __init__(self) -> None:
        """Инициализация обработчика."""
        self.model: ProductCategoryClassifier | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Инициализирован ModelHandler на устройстве: {self.device}")

    def initialize(self, context: Any) -> None:
        """
        Инициализация модели.

        Args:
            context: Контекст TorchServe с информацией о модели
        """
        logger.info("Начало инициализации модели...")

        # Получение пути к модели из контекста
        model_dir = context.system_properties.get("model_dir")
        if model_dir is None:
            # Попытка использовать переменную окружения или путь по умолчанию
            model_dir = os.getenv("MODEL_PATH", "models/checkpoint")

        model_path = Path(model_dir)

        # Если модель находится в архиве, ищем её в model_dir
        if not model_path.exists():
            # Попытка найти модель в стандартных местах
            possible_paths = [
                Path(model_dir) / "checkpoint",
                Path("models/checkpoint"),
                Path("/app/models/checkpoint"),
            ]
            for path in possible_paths:
                if path.exists():
                    model_path = path
                    break
            else:
                raise FileNotFoundError(f"Модель не найдена. Проверенные пути: {possible_paths}")

        logger.info(f"Загрузка модели из {model_path}")

        try:
            self.model = ProductCategoryClassifier.from_pretrained(model_path)
            logger.info("Модель успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}", exc_info=True)
            raise

    def preprocess(self, requests: list[Any]) -> list[list[str]]:
        """
        Предобработка запросов.

        Args:
            requests: Список запросов от TorchServe

        Returns:
            Список списков названий продуктов
        """
        product_titles_list: list[list[str]] = []

        for request in requests:
            # Парсинг JSON из байтов или строки
            if isinstance(request, bytes):
                data = json.loads(request.decode("utf-8"))
            elif isinstance(request, str):
                data = json.loads(request)
            else:
                data = request

            # Извлечение product_titles из запроса
            if isinstance(data, dict):
                if "product_titles" in data:
                    product_titles = data["product_titles"]
                elif "product_title" in data:
                    product_titles = [data["product_title"]]
                else:
                    raise ValueError(
                        f"Запрос должен содержать 'product_titles' или 'product_title'. "
                        f"Получено: {list(data.keys())}"
                    )
            elif isinstance(data, list):
                product_titles = data
            else:
                raise ValueError(f"Неожиданный формат данных: {type(data)}")

            # Нормализация: всегда список строк
            if isinstance(product_titles, str):
                product_titles = [product_titles]
            elif not isinstance(product_titles, list):
                product_titles = [str(product_titles)]

            product_titles_list.append(product_titles)

        logger.debug(f"Предобработано {len(product_titles_list)} запросов")
        return product_titles_list

    def inference(self, product_titles_list: list[list[str]]) -> list[dict[str, Any]]:
        """
        Выполнение предсказаний.

        Args:
            product_titles_list: Список списков названий продуктов

        Returns:
            Список словарей с результатами предсказаний
        """
        if self.model is None:
            raise RuntimeError("Модель не инициализирована")

        results: list[dict[str, Any]] = []

        for product_titles in product_titles_list:
            # Выполнение предсказаний
            predictions, confidences = self.model.predict_with_confidence(product_titles)

            # Формирование результата
            result = {
                "predictions": [
                    {
                        "product_title": title,
                        "predicted_category": pred,
                        "confidence": float(conf),
                    }
                    for title, pred, conf in zip(product_titles, predictions, confidences, strict=False)
                ]
            }

            results.append(result)

        logger.debug(f"Выполнено предсказаний для {len(results)} запросов")
        return results

    def postprocess(self, results: list[dict[str, Any]]) -> list[str]:
        """
        Постобработка результатов.

        Args:
            results: Список результатов предсказаний

        Returns:
            Список JSON строк с результатами
        """
        output: list[str] = []

        for result in results:
            output.append(json.dumps(result, ensure_ascii=False))

        return output

