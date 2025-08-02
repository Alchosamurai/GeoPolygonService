from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.polygon_service import PolygonService
import logging

router = APIRouter()
polygon_service = PolygonService()

logger = logging.getLogger(__name__)
class PointRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Широта в градусах")
    longitude: float = Field(..., ge=-180, le=180, description="Долгота в градусах")
    radius: float = Field(..., gt=0, le=50000, description="Радиус в метрах (максимум 50 км)")


class PolygonResponse(BaseModel):
    type: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


@router.get("/")
async def root():
    return {"message": "GeoPolygon API - сервис для создания полигонов покрытия"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/polygon", response_model=PolygonResponse)
async def create_polygon(request: PointRequest):
    logger.info("тест")
    try:
        result = await polygon_service.create_polygon(
            lat=request.latitude,
            lon=request.longitude,
            radius_meters=request.radius
        )
        
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"/polygon, params={request}, {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера") 