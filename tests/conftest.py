"""Конфигурация pytest для общих фикстур."""


import pandas as pd
import pytest


@pytest.fixture(scope="session")
def sample_product_data():
    """Создание тестового датасета продуктов для всех тестов."""
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
            ],
        }
    )
