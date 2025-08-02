from pydantic import BaseModel
from typing import Dict, Any

class PointRequest(BaseModel):
    latitude: float
    longitude: float
    radius: float

class PolygonResponse(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any] 