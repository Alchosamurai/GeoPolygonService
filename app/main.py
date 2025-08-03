from fastapi import FastAPI
from app.routes import router, sheets_router, cache_router, polygon_router
from app.config import settings
from app.database.database_init import init_database
import logging
from logging.handlers import RotatingFileHandler
import sys

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.include_router(router)
app.include_router(polygon_router)
app.include_router(sheets_router)
app.include_router(cache_router)



@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Starting GeoPolygon API...")
    try:
        # Инициализируем базу данных с PostGIS
        from init_db import init_postgis_database
        init_postgis_database()
        logger.info("PostGIS database initialized successfully")
        
        # Создаем таблицы приложения
        init_database()
        logger.info("Application tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Не прерываем запуск, так как база данных может быть недоступна


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('api.log', maxBytes=1024*1024, backupCount=5),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Уменьшаем уровень логгирования для некоторых библиотек
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)




if __name__ == "__main__":
    import uvicorn
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000) 