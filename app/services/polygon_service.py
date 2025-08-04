import asyncio
from typing import Dict, Optional
from app.services.geometry_service import GeometryService
from app.services.cache_service import CacheService
from app.services.sheets_service import SheetsService
from app.repositories.postgis_repository import PostgisRepository
from app.services.polygon_factory import CirclePolygon
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class PolygonService:
    def __init__(self):
        self.geometry_service = GeometryService()
        self.cache_service = CacheService()
        self.sheets_service = SheetsService()
        self.postgis_repository = PostgisRepository()

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
        cached_result = await self.cache_service.get_cached_polygon(lat, lon, radius_meters)
        if cached_result:
            # Логируем кэшированный запрос в Google Sheets
            asyncio.create_task(self._log_to_sheets(lat, lon, radius_meters, cached_result["area"]))
            logger.info(f"Returning cached polygon for coordinates ({lat}, {lon}) with radius {radius_meters}m")
            return {
                "polygon": cached_result["polygon"],
                "cached": True,
                "area": cached_result["area"]
            }
        
        # Имитируем долгий запрос
        await asyncio.sleep(settings.async_sleep_seconds)
        

        circle_polygon = CirclePolygon(lat, lon, radius_meters)
        await circle_polygon.initialize()
        result = circle_polygon.get_geojson_with_area()
        
        # Кэшируем результат
        await self.cache_service.cache_polygon(lat, lon, radius_meters, result["polygon"], result["area"])
        
        # Логируем в Google Sheets (асинхронно)
        asyncio.create_task(self._log_to_sheets(lat, lon, radius_meters, result["area"]))
        
        logger.info(f"Created new polygon for coordinates ({lat}, {lon}) with radius {radius_meters}m")
        return {
            "polygon": result["polygon"],
            "cached": False,
            "area": result["area"]
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
            await self.sheets_service.log_request(lat, lon, radius_meters, area)
        except Exception as e:
            logger.error(f"Error logging to sheets: {e}")

    async def get_cache_stats(self) -> Dict:
        """
        Получает статистику кэша
        
        Returns:
            Статистика кэша
        """
        return await self.cache_service.get_cache_stats()

    async def clear_cache(self) -> int:
        """
        Очищает весь кэш
        
        Returns:
            Количество удаленных записей
        """
        return await self.cache_service.clear_cache()

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

