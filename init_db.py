#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных PostgreSQL с расширением PostGIS
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import get_database_url
import logging

logger = logging.getLogger(__name__)

def init_postgis_database():
    """Инициализирует базу данных с расширением PostGIS"""
    
    # Парсим URL базы данных
    db_url = get_database_url()
    
    # Извлекаем параметры подключения
    # postgresql://user:password@host:port/database
    parts = db_url.replace('postgresql://', '').split('/')
    credentials_host = parts[0]
    database = parts[1]
    
    user_pass, host_port = credentials_host.split('@')
    user, password = user_pass.split(':')
    host, port = host_port.split(':')
    
    try:
        # Подключаемся к PostgreSQL серверу (не к конкретной базе данных)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Подключаемся к системной базе данных
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем, существует ли база данных
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database: {database}")
            cursor.execute(f"CREATE DATABASE {database}")
            logger.info(f"Database {database} created successfully")
        else:
            logger.info(f"Database {database} already exists")
        
        cursor.close()
        conn.close()
        
        # Теперь подключаемся к созданной базе данных
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем, установлено ли расширение PostGIS
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
        postgis_exists = cursor.fetchone()
        
        if not postgis_exists:
            logger.info("Installing PostGIS extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            logger.info("PostGIS extension installed successfully")
        else:
            logger.info("PostGIS extension already installed")
        
        cursor.close()
        conn.close()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_postgis_database() 