from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.polygon_service import PolygonService
from app.models import *
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
polygon_router = APIRouter(tags=["Построение полигона 🗺️"])
cache_router = APIRouter(tags=["Работа с кешем ⚙️"])
sheets_router = APIRouter(tags=["Работа с гугл-таблицами 📚"])
polygon_service = PolygonService()


@router.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "GeoPolygon API - сервис для создания полигонов покрытия"}


@router.get("/health")
async def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}


@polygon_router.post("/polygon", response_model=PolygonResponse)
async def create_polygon(request: PointRequest):
    logger.info(f"Creating polygon for coordinates ({request.latitude}, {request.longitude}) with radius {request.radius}m")
    
    try:
        result = await polygon_service.create_polygon(
            lat=request.latitude,
            lon=request.longitude,
            radius_meters=request.radius
        )
        
        logger.info(f"Successfully created polygon with area {result['area']:.2f} m²")
        
        return {
            "type": "Feature",
            "geometry": result["polygon"],
            "properties": {
                "center": [request.longitude, request.latitude],
                "radius": request.radius,
                "area_sqm": result["area"],
                "cached": result["cached"]
            }
        }
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating polygon: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@polygon_router.post('/perfomance-test')
async def stress_test(request: PointRequest):
    logger.info(f"Creating polygon for coordinates ({request.latitude}, {request.longitude}) with radius {request.radius}m")
    for i in range(0,20):
        await polygon_service.create_polygon(
            lat=request.latitude,
            lon=request.longitude,
            radius_meters=request.radius
        )
    return {"status": "ok", "message": f"Было выполнено 20 асинхронных запросов"}
@sheets_router.post("/spreadsheet", response_model=SpreadsheetResponse)
async def create_spreadsheet():
    """Создает новую Google таблицу для логирования запросов"""
    logger.info("Creating new Google Spreadsheet")
    
    spreadsheet_id = polygon_service.create_spreadsheet()
    if not spreadsheet_id:
        logger.error("Failed to create Google Spreadsheet")
        raise HTTPException(status_code=500, detail="Не удалось создать Google таблицу")
    
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    logger.info(f"Successfully created Google Spreadsheet: {spreadsheet_id}")
    
    return SpreadsheetResponse(spreadsheet_id=spreadsheet_id, url=url)


@sheets_router.get("/spreadsheet/url")
async def get_spreadsheet_url():
    """Возвращает URL текущей Google таблицы"""
    logger.debug("Getting Google Spreadsheet URL")
    
    url = polygon_service.get_spreadsheet_url()
    if not url:
        logger.warning("Google Spreadsheet URL not found")
        raise HTTPException(status_code=404, detail="Google таблица не настроена")
    
    return {"url": url}


@cache_router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Возвращает статистику кэша"""
    logger.debug("Getting cache statistics")
    
    stats = polygon_service.get_cache_stats()
    return CacheStatsResponse(**stats)


@cache_router.delete("/cache")
async def clear_cache():
    """Очищает весь кэш"""
    logger.info("Clearing cache")
    
    deleted_count = polygon_service.clear_cache()
    logger.info(f"Cleared {deleted_count} cache entries")
    
    return {"deleted_entries": deleted_count}


@cache_router.delete("/cache/entry")
async def delete_cache_entry(lat: float, lon: float, radius: float):
    """Удаляет конкретную запись кэша"""
    logger.info(f"Deleting cache entry for coordinates ({lat}, {lon}) with radius {radius}m")
    
    success = polygon_service.cache_service.delete_cache_entry(lat, lon, radius)
    if not success:
        logger.warning(f"Cache entry not found for coordinates ({lat}, {lon}) with radius {radius}m")
        raise HTTPException(status_code=404, detail="Запись кэша не найдена")
    
    return {"message": "Cache entry deleted successfully"}



