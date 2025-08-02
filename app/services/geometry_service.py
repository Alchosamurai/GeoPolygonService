import math
import logging
from typing import Dict
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj

logger = logging.getLogger(__name__)

class GeometryService:
    def __init__(self):
        self.earth_radius = 6371000  # радиус Земли в метрах
    
    def create_circular_polygon(self, lat: float, lon: float, radius_meters: float, num_points: int = 64) -> Dict:
        """
        Создает круговой полигон с заданным радиусом вокруг точки
        
        Args:
            lat: широта центральной точки
            lon: долгота центральной точки  
            radius_meters: радиус в метрах
            num_points: количество точек для аппроксимации круга
            
        Returns:
            GeoJSON полигон
        """
        center_point = Point(lon, lat)
        
        # Создаем круг в проекции UTM для точности
        utm_proj = self._get_utm_projection(lon, lat)
        wgs84_proj = pyproj.Proj('EPSG:4326')
        
        # Трансформируем центр в UTM
        transformer = pyproj.Transformer.from_proj(wgs84_proj, utm_proj, always_xy=True)
        center_utm = transform(transformer.transform, center_point)
        
        # Создаем круг в UTM координатах
        circle_utm = center_utm.buffer(radius_meters, quad_segs=num_points)
        
        # Трансформируем обратно в WGS84
        transformer_back = pyproj.Transformer.from_proj(utm_proj, wgs84_proj, always_xy=True)
        circle_wgs84 = transform(transformer_back.transform, circle_utm)
        
        # Конвертируем в GeoJSON
        coords = list(circle_wgs84.exterior.coords)
        
        return {
            "type": "Polygon",
            "coordinates": [coords]
        }
    
    def calculate_polygon_area(self, polygon_geojson: Dict) -> float:
        """
        Вычисляет площадь полигона в квадратных метрах
        
        Args:
            polygon_geojson: GeoJSON полигон
            
        Returns:
            Площадь в квадратных метрах
        """
        coords = polygon_geojson["coordinates"][0]
        polygon = Polygon(coords)
        

        # Используем равновеликую проекцию для точного расчета площади
        # center_lon = sum(coord[0] for coord in coords) / len(coords)
        # center_lat = sum(coord[1] for coord in coords) / len(coords)
        
        #в прошлом подходе юзалось среднеарифметическое, что могло создавать погрешность, теперь более корректно 
        center_lon, center_lat = self.calculate_albers_center_by_polygon(polygon)
        
        # Проверяем экстремальные случаи
        if abs(center_lat) > 85:
            # Для полюсов используем простую формулу площади
            return self._calculate_simple_area(polygon_geojson)
        
        # Ограничиваем значения широты для корректной работы проекции
        lat_1 = max(-85, center_lat - 5)
        lat_2 = min(85, center_lat + 5)
        lat_0 = max(-85, min(85, center_lat))
        
        #Равновеликая коническая проекция Альберса - см. базу знаний
        area_proj = pyproj.Proj(f"+proj=aea +lat_1={lat_1} +lat_2={lat_2} +lat_0={lat_0} +lon_0={center_lon}")
        wgs84_proj = pyproj.Proj('EPSG:4326')
        
        transformer = pyproj.Transformer.from_proj(wgs84_proj, area_proj, always_xy=True)
        polygon_projected = transform(transformer.transform, polygon)
        
        return polygon_projected.area
    
    @staticmethod
    def calculate_albers_center_by_polygon(polygon: Polygon):
        centroid = polygon.centroid
        return centroid.x, centroid.y
    
    def _calculate_simple_area(self, polygon_geojson: Dict) -> float:
        """
        Простой расчет площади для экстремальных случаев
        
        Args:
            polygon_geojson: GeoJSON полигон
            
        Returns:
            Приблизительная площадь в квадратных метрах
        """
        coords = polygon_geojson["coordinates"][0]
        
        # Используем формулу Гаусса для расчета площади на сфере
        area = 0
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]
            
            # Конвертируем в радианы
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            dlon = math.radians(lon2 - lon1)
            
            # Формула площади на сфере
            area += self.earth_radius**2 * abs(
                math.sin(lat1_rad) * math.sin(lat2_rad) * math.cos(dlon) +
                math.cos(lat1_rad) * math.cos(lat2_rad)
            )
        return area
    
    def _get_utm_projection(self, lon: float, lat: float) -> pyproj.Proj:
        """
        Определяет UTM зону для заданных координат
        
        Args:
            lon: долгота
            lat: широта
            
        Returns:
            UTM проекция
        """
        utm_zone = int((lon + 180) / 6) + 1
        hemisphere = 'north' if lat >= 0 else 'south'
        
        return pyproj.Proj(f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84")
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Валидирует координаты
        
        Args:
            lat: широта
            lon: долгота
            
        Returns:
            True если координаты валидны
        """
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    def validate_radius(self, radius_meters: float) -> bool:
        """
        Валидирует радиус
        Ограничение на радиус до 50км
        
        Args:
            radius_meters: радиус в метрах
            
        Returns:
            True если радиус валиден
        """
        #GSM (2G) - самая "дальнобойная" вышка, имеет радиус действия до 35 км в идеальных условиях
        #Поставил ограничение на радиус полигона до 50к для меньшей нагрузки на сервис, а также для защиты от фрода)
        return 0 < radius_meters <= 50000  