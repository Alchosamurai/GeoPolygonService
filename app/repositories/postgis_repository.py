import json
import asyncio
from typing import Optional, Dict, List
from app.database.database import engine
import geopandas as gpd
import logging

logger = logging.getLogger(__name__)

class PostgisRepository:
    def __init__(self):
        pass
    
    async def create_circle_polygon_with_area(self, lat: float, lon: float, radius_meters: float) -> Dict:
        """
        Создает полигон силами базы данных, возвращает геометрию и площадь в метрах
        """
        try:
            from app.config import settings
            segments = settings.default_polygon_points
            
            def _create_polygon():
                # Используем UTM проекцию для более точных расчетов
                # Определяем UTM зону на основе долготы
                utm_zone = int((lon + 180) / 6) + 1
                epsg_code = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone
                
                # Для крайних случаев используем более безопасную проекцию
                if abs(lat) > 80 or abs(lon) > 175:
                    # Используем полярную стереографическую проекцию для крайних случаев
                    epsg_code = 3413 if lat > 0 else 3412  # NSIDC Sea Ice Polar Stereographic
                
                query = f"""
                    WITH circle AS (
                        SELECT 
                            ST_Buffer(
                                ST_Transform(
                                    ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326),
                                    {epsg_code}  -- Более подходящая проекция
                                ),
                                {radius_meters},
                                {segments}  -- Количество сегментов для аппроксимации круга
                            ) AS geom
                    )
                    SELECT 
                        ST_Transform(geom, 4326) AS geom,
                        ST_Area(geom) AS area
                    FROM circle;
                    """
                
                # Используем engine напрямую для geopandas
                result = gpd.read_postgis(query, engine, geom_col='geom')
                
                # Получаем геометрию и площадь из результата
                geom = result['geom'].iloc[0]
                area = float(result['area'].iloc[0])
                
                # Преобразуем геометрию в GeoJSON
                geom_json = {
                    "type": geom.geom_type,
                    "coordinates": geom.__geo_interface__["coordinates"]
                }
                
                return {
                    "geometry": geom_json,
                    "area_sqm": area
                }
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _create_polygon)
            
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
        
