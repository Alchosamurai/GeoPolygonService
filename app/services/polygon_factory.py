from app.services import GeometryService
from app.repositories.postgis_repository import PostgisRepository
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class CirclePolygon:
    def __init__(self, lat: float, lon: float, radius_m: float, points: int = 64) -> None:
        self.lat = lat
        self.lon = lon
        self.radius_m = radius_m
        self.points = points
        self._geometry_service = GeometryService()
        self._postgis = PostgisRepository()
        self._geoJSON = None 
        self._area = None 

    async def initialize(self) -> None:
        """Асинхронная инициализация полигона"""
        await self._create_polygon()

    async def _create_polygon(self) -> None:
        try:
            await self._create_polygon_by_postgis()
        except Exception as e:
            logger.warning(f"Ошибка построения полигона lat={self.lat}, lon={self.lon}, rad={self.radius_m} в postGIS: {e}, построение через pyproj")
            self._create_polygon_by_pyproj()

    def _create_polygon_by_pyproj(self)-> None:
        """Создает полигон локально через pyproj"""
        self._geoJSON = self._geometry_service.create_circular_polygon(self.lat, self.lon, self.radius_m, self.points)
        self._area = self._geometry_service.calculate_polygon_area(self._geoJSON)

    async def _create_polygon_by_postgis(self) -> None:
        """
        Создает апроксимирующий круг полигон через PostGIS
        Заполняет атрибуты класса
        """
        response = await self._postgis.create_circle_polygon_with_area(self.lat, self.lon, self.radius_m)
        self._geoJSON = response['geometry']
        self._area = response['area_sqm']

    async def recalculate_polygon(self):
        """
        Если у объекта изменились координаты/радиус, можно перестроить полигон и пересчитать его площадь
        """
        await self._create_polygon()

    def get_geojson_with_area(self) -> Dict:
        """Возвращает результат с площадью"""
        return {
            "polygon": self._geoJSON,
            "cached": False,
            "area": self._area
        }
    
    @property
    def geoJSON(self) -> Dict:
        return self._geoJSON
    
    @property
    def area(self) -> float:
        return self._area

    def __str__(self) -> str:
        area_str = f"{self.area:.2f}m²" if self.area is not None else "не рассчитана"
        return f"CirclePolygon(center=({self.lat}, {self.lon}), radius={self.radius_m}m, area={area_str})"

    def __repr__(self) -> str:
        return self.__str__()
