from fastapi import APIRouter
from models import PointRequest, PolygonResponse

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "GeoPolygon API работает!"}

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.post("/polygon", response_model=PolygonResponse)
async def create_polygon(request: PointRequest):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
        },
        "properties": {
            "center": [request.longitude, request.latitude],
            "radius": request.radius
        }
    } 