import asyncio
from typing import Dict
from app.services.geometry_service import GeometryService


class PolygonService:
    def __init__(self):
        self.geometry_service = GeometryService()
    
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
        
        
        # Имитируем долгий запрос
        await asyncio.sleep(5)
        
        # Создаем полигон
        polygon = self.geometry_service.create_circular_polygon(lat, lon, radius_meters)
        area = self.geometry_service.calculate_polygon_area(polygon)
        
        return {
            "polygon": polygon,
            "cached": False,
            "area": area
        }

