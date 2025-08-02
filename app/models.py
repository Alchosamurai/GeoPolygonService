from pydantic import BaseModel, Field
from typing import Dict, Any

class PointRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Широта в градусах")
    longitude: float = Field(..., ge=-180, le=180, description="Долгота в градусах")
    radius: float = Field(..., gt=0, description="Радиус в метрах")


class PolygonResponse(BaseModel):
    type: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class SpreadsheetResponse(BaseModel):
    spreadsheet_id: str
    url: str


class CacheStatsResponse(BaseModel):
    total_cached_polygons: int

