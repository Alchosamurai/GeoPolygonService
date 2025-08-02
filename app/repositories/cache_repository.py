import json
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models import CacheEntry
from app.database.database import get_db
import logging

logger = logging.getLogger(__name__)


class CacheRepository:
    def __init__(self):
        pass
    
    def get_by_cache_key(self, cache_key: str) -> Optional[CacheEntry]:
        """
        Получает запись кэша по ключу
        
        Args:
            cache_key: ключ кэша
            
        Returns:
            Запись кэша или None
        """
        db = next(get_db())
        try:
            cache_entry = db.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
            if cache_entry:
                logger.debug(f"Cache hit for key: {cache_key}")
            else:
                logger.debug(f"Cache miss for key: {cache_key}")
            return cache_entry
        finally:
            db.close()
    
    def create_cache_entry(self, cache_key: str, lat: float, lon: float, 
                          radius_meters: float, polygon_data: Dict, area: float) -> CacheEntry:
        """
        Создает новую запись в кэше
        
        Args:
            cache_key: ключ кэша
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            polygon_data: GeoJSON полигон
            area: площадь полигона
            
        Returns:
            Созданная запись кэша
        """
        db = next(get_db())
        try:
            cache_entry = CacheEntry(
                cache_key=cache_key,
                latitude=lat,
                longitude=lon,
                radius_meters=radius_meters,
                polygon_data=json.dumps(polygon_data),
                area_sqm=area
            )
            db.add(cache_entry)
            db.commit()
            db.refresh(cache_entry)
            
            logger.info(f"Created cache entry for key: {cache_key}")
            return cache_entry
        finally:
            db.close()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Получает статистику кэша
        
        Returns:
            Словарь со статистикой
        """
        db = next(get_db())
        try:
            total_entries = db.query(CacheEntry).count()
            
            # Статистика по радиусам
            radius_stats = db.query(
                CacheEntry.radius_meters,
                func.count(CacheEntry.id)
            ).group_by(CacheEntry.radius_meters).all()
            
            logger.debug(f"Cache stats: {total_entries} total entries")
            
            return {
                "total_cached_polygons": total_entries,
                "radius_distribution": dict(radius_stats)
            }
        finally:
            db.close()
    
    def clear_cache(self) -> int:
        """
        Очищает весь кэш
        
        Returns:
            Количество удаленных записей
        """
        db = next(get_db())
        try:
            deleted_count = db.query(CacheEntry).delete()
            db.commit()
            
            logger.info(f"Cleared cache: {deleted_count} entries deleted")
            return deleted_count
        finally:
            db.close()
    
    def get_oldest_entries(self, limit: int = 10) -> List[CacheEntry]:
        """
        Получает самые старые записи кэша
        
        Args:
            limit: максимальное количество записей
            
        Returns:
            Список старых записей
        """
        db = next(get_db())
        try:
            entries = db.query(CacheEntry).order_by(CacheEntry.created_at.asc()).limit(limit).all()
            return entries
        finally:
            db.close()
    
    def delete_by_cache_key(self, cache_key: str) -> bool:
        """
        Удаляет запись кэша по ключу
        
        Args:
            cache_key: ключ кэша
            
        Returns:
            True если запись была удалена
        """
        db = next(get_db())
        try:
            result = db.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).delete()
            db.commit()
            
            if result:
                logger.info(f"Deleted cache entry for key: {cache_key}")
            else:
                logger.warning(f"Cache entry not found for key: {cache_key}")
            
            return result > 0
        finally:
            db.close() 