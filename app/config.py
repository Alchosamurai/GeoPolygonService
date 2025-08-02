import os
from typing import Optional
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


#для тестового задания не вижу смысла прятать все данные
class Settings(BaseSettings):
    # Основные настройки приложения
    app_name: str = "GeoPolygon API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Настройки базы данных
    database_url: str = "postgresql://postgres:root@localhost:5432/GeoPoly"
    
    # Настройки Google Sheets
    google_service_account_file: str = "service-account-key.json"
    google_spreadsheet_id: Optional[str] = "1RfBJV3OcWtf9M-jBxbkAXQsvUwpMvzHyjZRmwuIaM1Y"
    
    # Настройки геометрии
    max_radius_meters: float = 50000.0  # 50 км по умолчанию
    default_polygon_points: int = 64
    
    # Настройки производительности
    async_sleep_seconds: int = 5  # время имитации долгого запроса
    
    # Настройки логирования
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем глобальный экземпляр настроек
settings = Settings()

logger.info(f"Application configuration loaded: {settings.app_name} v{settings.app_version}")


def get_database_url() -> str:
    """Возвращает URL базы данных"""
    return settings.database_url


def get_google_config() -> dict:
    """Возвращает конфигурацию Google Sheets"""
    return {
        "service_account_file": settings.google_service_account_file,
        "spreadsheet_id": settings.google_spreadsheet_id
    }


def get_geometry_config() -> dict:
    """Возвращает конфигурацию геометрии"""
    return {
        "max_radius": settings.max_radius_meters,
        "default_points": settings.default_polygon_points
    }


def is_google_sheets_enabled() -> bool:
    """Проверяет, включена ли интеграция с Google Sheets"""
    is_enabled = (
        os.path.exists(settings.google_service_account_file) and 
        settings.google_spreadsheet_id is not None
    )
    
    if is_enabled:
        logger.info("Google Sheets integration is enabled")
    else:
        logger.warning("Google Sheets integration is disabled")
    
    return is_enabled 