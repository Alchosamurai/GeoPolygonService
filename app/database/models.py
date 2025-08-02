from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
from app.database.database import Base


class CacheEntry(Base):
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False)
    polygon_data = Column(String, nullable=False)  # JSON строка
    area_sqm = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())