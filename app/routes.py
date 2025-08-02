from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.polygon_service import PolygonService
from app.models import *
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
polygon_service = PolygonService()



@router.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "GeoPolygon API - сервис для создания полигонов покрытия"}


@router.get("/health")
async def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}


@router.post("/polygon", response_model=PolygonResponse)
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


@router.post("/spreadsheet", response_model=SpreadsheetResponse)
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


@router.get("/spreadsheet/url")
async def get_spreadsheet_url():
    """Возвращает URL текущей Google таблицы"""
    logger.debug("Getting Google Spreadsheet URL")
    
    url = polygon_service.get_spreadsheet_url()
    if not url:
        logger.warning("Google Spreadsheet URL not found")
        raise HTTPException(status_code=404, detail="Google таблица не настроена")
    
    return {"url": url}



