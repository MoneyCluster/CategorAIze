"""Тесты для модуля обучения."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from categoraize.training.trainer import Trainer


@pytest.fixture
def sample_data():
    """Создание тестового датасета."""
    return pd.DataFrame(
        {
            "product_title": [
                "iPhone 15 Pro Max",
                "Samsung Galaxy S24",
                "Laptop Dell XPS 13",
                "MacBook Pro M3",
                "iPad Air",
                "Surface Pro",
                "Pixel 8",
                "ThinkPad X1",
                "OnePlus 12",
                "HP Spectre x360",
                "iPad Pro",
                "Surface Laptop",
            ],
            "category": [
                "Electronics",
                "Electronics",
                "Computers",
                "Computers",
                "Tablets",
                "Computers",
                "Electronics",
                "Computers",
                "Electronics",
                "Computers",
                "Tablets",
                "Computers",
            ],
        }
    )


@pytest.fixture
def temp_data_dir(sample_data):
    """Создание временной директории с тестовыми данными."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "product_titles.csv"
        sample_data.to_csv(data_path, index=False)

        # Создаем конфигурацию
        config = {
            "data": {
                "path": tmpdir,
                "filename": "product_titles.csv",
                # Используем стандартные названия колонок для тестов
            },
            "preprocessing": {"lowercase": True, "remove_punctuation": False},
            "split": {"test_size": 0.2, "val_size": 0.1, "random_seed": 42},
            "model": {
                "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "classifier_type": "lr",
                "classifier_params": {"max_iter": 100},
            },
            "output": {"model_path": str(Path(tmpdir) / "models" / "checkpoint")},
        }

        yield tmpdir, config


class TestTrainer:
    """Тесты для класса Trainer."""

    def test_init(self, temp_data_dir):
        """Тест инициализации Trainer."""
        _, config = temp_data_dir
        trainer = Trainer(config)
        assert trainer.config == config
        assert trainer.model is None

    def test_load_data(self, temp_data_dir):
        """Тест загрузки данных."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)

        df = trainer.load_data()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12  # Обновлено: в фикстуре теперь 12 записей
        assert "product_title" in df.columns
        assert "category" in df.columns

    def test_preprocess_data(self, temp_data_dir):
        """Тест предобработки данных."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)
        df = trainer.load_data()

        df_processed = trainer.preprocess_data(df)

        assert isinstance(df_processed, pd.DataFrame)
        assert len(df_processed) <= len(df)
        assert df_processed["product_title"].iloc[0].islower()

    def test_split_data(self, temp_data_dir):
        """Тест разделения данных."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)
        df = trainer.load_data()
        df_processed = trainer.preprocess_data(df)

        X_train, X_val, X_test, y_train, y_val, y_test, id_to_label = trainer.split_data(
            df_processed
        )

        assert len(X_train) > 0
        assert len(X_val) > 0
        assert len(X_test) > 0
        assert len(X_train) + len(X_val) + len(X_test) == len(df_processed)
        assert isinstance(id_to_label, dict)

    def test_create_model(self, temp_data_dir):
        """Тест создания модели."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)

        model = trainer.create_model()

        assert model is not None
        assert trainer.model is not None
        assert model.classifier_type == "lr"

    def test_train(self, temp_data_dir):
        """Тест обучения модели."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)
        df = trainer.load_data()
        df_processed = trainer.preprocess_data(df)
        X_train, X_val, X_test, y_train, y_val, y_test, _ = trainer.split_data(df_processed)
        trainer.create_model()

        model = trainer.train(X_train, y_train, use_class_weights=False)

        assert model.is_fitted is True
        assert model.id_to_label is not None

    def test_train_with_class_weights(self, temp_data_dir):
        """Тест обучения с весами классов."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)
        df = trainer.load_data()
        df_processed = trainer.preprocess_data(df)
        X_train, X_val, X_test, y_train, y_val, y_test, _ = trainer.split_data(df_processed)
        trainer.create_model()

        model = trainer.train(X_train, y_train, use_class_weights=True)

        assert model.is_fitted is True

    def test_save_model(self, temp_data_dir):
        """Тест сохранения модели."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)
        df = trainer.load_data()
        df_processed = trainer.preprocess_data(df)
        X_train, X_val, X_test, y_train, y_val, y_test, _ = trainer.split_data(df_processed)
        trainer.create_model()
        trainer.train(X_train, y_train)

        save_path = Path(tmpdir) / "saved_model"
        trainer.save_model(save_path)

        assert save_path.exists()
        assert (save_path / "classifier.joblib").exists()
        assert (save_path / "metadata.json").exists()

    def test_run_training(self, temp_data_dir):
        """Тест полного пайплайна обучения."""
        tmpdir, config = temp_data_dir
        trainer = Trainer(config)

        model, validation_data = trainer.run_training()

        assert model.is_fitted is True
        assert "X_val" in validation_data
        assert "y_val" in validation_data
        assert "X_test" in validation_data
        assert "y_test" in validation_data
        assert len(validation_data["X_val"]) > 0
        assert len(validation_data["X_test"]) > 0
