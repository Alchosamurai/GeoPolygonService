from fastapi import FastAPI
from app.routes import router
import logging
from logging.handlers import RotatingFileHandler
import sys

app = FastAPI(title="GeoPolygon API", version="1.0.0")

app.include_router(router)

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