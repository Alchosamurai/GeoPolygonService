from app.database.database import engine
from app.database.models import Base
import logging

logger = logging.getLogger(__name__)


def init_database():
    """Создает все таблицы в базе данных"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


if __name__ == "__main__":
    init_database() 