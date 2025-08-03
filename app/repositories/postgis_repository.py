import json
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database.models import CacheEntry
from app.database.database import get_db, engine
import geopandas as gpd
import logging

logger = logging.getLogger(__name__)

class PostgisRepository:
    def __init__(self):
        self.db = next(get_db())
    
    def create_polygon(self, lat: float, lon: float, radius_meters: float) -> Dict:
        """
        Создает полигон в базе данных
        """
        try:
            from app.config import settings
            segments = settings.default_polygon_points
            query = """
                WITH circle AS (
                    SELECT 
                        ST_Buffer(
                            ST_Transform(
                                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                                3857  -- Проекция Web Mercator для работы в метрах
                            ),
                            %s,
                            %s  -- Количество сегментов для аппроксимации круга
                        ) AS geom
                )
                SELECT 
                    ST_Transform(geom, 4326) AS geom,
                    ST_Area(geom) AS area
                FROM circle;
                """
            
            # Используем engine напрямую для geopandas с параметрами
            result = gpd.read_postgis(query, engine, params=(lon, lat, radius_meters, segments), geom_col='geom')
            
            # Получаем геометрию и площадь из результата
            geom = result['geom'].iloc[0]
            area = float(result['area'].iloc[0])
            
            # Преобразуем геометрию в GeoJSON
            geom_json = {
                "type": geom.geom_type,
                "coordinates": geom.__geo_interface__["coordinates"]
            }
            
            result_dict = {
                "geometry": geom_json,
                "area_sqm": area
            }
            return result_dict
            
        except Exception as e:
            logger.error(f"Error creating polygon in database: {e}")
            # Если база данных недоступна, используем fallback
            from app.services.geometry_service import GeometryService
            geometry_service = GeometryService()
            polygon = geometry_service.create_circular_polygon(lat, lon, radius_meters)
            area = geometry_service.calculate_polygon_area(polygon)
            
            return {
                "geometry": polygon,
                "area_sqm": area
            }
        
