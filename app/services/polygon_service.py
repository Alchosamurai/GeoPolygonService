import asyncio
from typing import Dict, Optional
from app.services.geometry_service import GeometryService
from app.services.cache_service import CacheService
from app.services.sheets_service import SheetsService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class PolygonService:
    def __init__(self):
        self.geometry_service = GeometryService()
        self.cache_service = CacheService()
        self.sheets_service = SheetsService()
    
    async def create_polygon(self, lat: float, lon: float, radius_meters: float) -> Dict:
        """
        Создает полигон покрытия с заданными параметрами
        
        Args:
            lat: широта центральной точки
            lon: долгота центральной точки
            radius_meters: радиус в метрах
            
        Returns:
            Словарь с результатом операции
        """
        # Валидация входных данных
        if not self.geometry_service.validate_coordinates(lat, lon):
            raise ValueError("Некорректные координаты")
        
        if not self.geometry_service.validate_radius(radius_meters):
            raise ValueError("Некорректный радиус")
        
        # Проверяем кэш
        cached_polygon = self.cache_service.get_cached_polygon(lat, lon, radius_meters)
        if cached_polygon:
            area = self.geometry_service.calculate_polygon_area(cached_polygon)
            # Логируем кэшированный запрос в Google Sheets
            asyncio.create_task(self._log_to_sheets(lat, lon, radius_meters, area))
            logger.info(f"Returning cached polygon for coordinates ({lat}, {lon}) with radius {radius_meters}m")
            return {
                "polygon": cached_polygon,
                "cached": True,
                "area": area
            }
        
        # Имитируем долгий запрос
        await asyncio.sleep(settings.async_sleep_seconds)
        
        # Создаем полигон
        polygon = self.geometry_service.create_circular_polygon(lat, lon, radius_meters)
        area = self.geometry_service.calculate_polygon_area(polygon)
        
        # Кэшируем результат
        self.cache_service.cache_polygon(lat, lon, radius_meters, polygon, area)
        
        # Логируем в Google Sheets (асинхронно)
        asyncio.create_task(self._log_to_sheets(lat, lon, radius_meters, area))
        
        logger.info(f"Created new polygon for coordinates ({lat}, {lon}) with radius {radius_meters}m")
        return {
            "polygon": polygon,
            "cached": False,
            "area": area
        }
    
    async def _log_to_sheets(self, lat: float, lon: float, radius_meters: float, area: float):
        """
        Асинхронно логирует запрос в Google Sheets
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            area: площадь полигона
        """
        try:
            self.sheets_service.log_request(lat, lon, radius_meters, area)
        except Exception as e:
            logger.error(f"Error logging to sheets: {e}")
    
    def get_cache_stats(self) -> Dict:
        """
        Получает статистику кэша
        
        Returns:
            Статистика кэша
        """
        return self.cache_service.get_cache_stats()
    
    def clear_cache(self) -> int:
        """
        Очищает весь кэш
        
        Returns:
            Количество удаленных записей
        """
        return self.cache_service.clear_cache()
    
    def create_spreadsheet(self) -> Optional[str]:
        """
        Создает новую Google таблицу для логирования
        
        Returns:
            ID созданной таблицы
        """
        return self.sheets_service.create_spreadsheet()
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """
        Возвращает URL Google таблицы
        
        Returns:
            URL таблицы
        """
        return self.sheets_service.get_spreadsheet_url()

