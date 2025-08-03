import hashlib
import json
from typing import Optional, Dict, Any
from app.repositories.cache_repository import CacheRepository
import logging

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.repository = CacheRepository()
    
    def _generate_cache_key(self, lat: float, lon: float, radius_meters: float) -> str:
        """
        Генерирует ключ кэша на основе параметров запроса
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            
        Returns:
            Хэш ключ для кэша
        """
        data = {
            "lat": round(lat, 6),
            "lon": round(lon, 6), 
            "radius": round(radius_meters, 2)
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    async def get_cached_polygon(self, lat: float, lon: float, radius_meters: float) -> Optional[Dict]:
        """
        Получает полигон из кэша
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            
        Returns:
            Кэшированный GeoJSON или None
        """
        cache_key = self._generate_cache_key(lat, lon, radius_meters)
        
        cache_entry = await self.repository.get_by_cache_key(cache_key)
        if cache_entry:
            try:
                polygon_data = json.loads(cache_entry.polygon_data)
                logger.info(f"Cache hit for coordinates ({lat}, {lon}) with radius {radius_meters}m")
                return {
                    "polygon": polygon_data,
                    "area": cache_entry.area_sqm
                }
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing cached polygon data: {e}")
                return None
        
        logger.debug(f"Cache miss for coordinates ({lat}, {lon}) with radius {radius_meters}m")
        return None
    def get_cashed_data(self, lat: float, lon: float, radius_meters: float) -> Optional[Dict]:
        """
        Получает данные из кэша
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            
        Returns:
            Кэшированный GeoJSON и прочие данные или None
        """
        cache_key = self._generate_cache_key(lat, lon, radius_meters)
        
        cache_entry = self.repository.get_by_cache_key(cache_key)
        if cache_entry:
            logger.info(f"Cache hit for coordinates ({lat}, {lon}) with radius {radius_meters}m")
            return cache_entry
        logger.debug(f"Cache miss for coordinates ({lat}, {lon}) with radius {radius_meters}m")
        return None


    async def cache_polygon(self, lat: float, lon: float, radius_meters: float, polygon_data: Dict, area: float) -> None:
        """
        Сохраняет полигон в кэш
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            polygon_data: GeoJSON полигон
            area: площадь полигона
        """
        cache_key = self._generate_cache_key(lat, lon, radius_meters)
        
        try:
            await self.repository.create_cache_entry(
                cache_key=cache_key,
                lat=lat,
                lon=lon,
                radius_meters=radius_meters,
                polygon_data=polygon_data,
                area=area
            )
            logger.info(f"Cached polygon for coordinates ({lat}, {lon}) with radius {radius_meters}m")
        except Exception as e:
            logger.error(f"Error caching polygon: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Получает статистику кэша
        
        Returns:
            Статистика кэша
        """
        return await self.repository.get_cache_stats()
    
    async def clear_cache(self) -> int:
        """
        Очищает весь кэш
        
        Returns:
            Количество удаленных записей
        """
        return await self.repository.clear_cache()
    
    def delete_cache_entry(self, lat: float, lon: float, radius_meters: float) -> bool:
        """
        Удаляет конкретную запись кэша
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            
        Returns:
            True если запись была удалена
        """
        cache_key = self._generate_cache_key(lat, lon, radius_meters)
        return self.repository.delete_by_cache_key(cache_key) 