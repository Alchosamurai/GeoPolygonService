import os
from datetime import datetime
from typing import Dict, Any, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import get_google_config, is_google_sheets_enabled
import logging

logger = logging.getLogger(__name__)


class SheetsService:
    def __init__(self):
        self.scope = ['https://www.googleapis.com/auth/spreadsheets']
        self.credentials = None
        self.service = None
        self.config = get_google_config()
        self.spreadsheet_id = self.config.get('spreadsheet_id')
        self._initialize_service()
    
    def _initialize_service(self):
        """Инициализирует сервис Google Sheets"""
        if not is_google_sheets_enabled():
            logger.warning("Google Sheets integration is disabled - missing configuration")
            return
            
        try:
            service_account_file = self.config.get('service_account_file')
            
            if os.path.exists(service_account_file):
                self.credentials = Credentials.from_service_account_file(
                    service_account_file, scopes=self.scope
                )
                self.service = build('sheets', 'v4', credentials=self.credentials)
                logger.info("Google Sheets service initialized successfully")
            else:
                logger.warning(f"Service account file {service_account_file} not found")
        except Exception as e:
            logger.error(f"Error initializing Google Sheets service: {e}")
    
    async def log_request(self, lat: float, lon: float, radius_meters: float, area_sqm: float) -> bool:
        """
        Записывает информацию о запросе в Google Sheets
        
        Args:
            lat: широта
            lon: долгота
            radius_meters: радиус в метрах
            area_sqm: площадь полигона
            
        Returns:
            True если запись успешна
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available")
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            values = [
                [
                    timestamp,
                    f"{lat:.6f}",
                    f"{lon:.6f}", 
                    f"{radius_meters:.2f}",
                    f"{area_sqm:.2f}"
                ]
            ]
            
            range_name = 'A:E'
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Logged request to Google Sheets: {result.get('updates').get('updatedCells')} cells updated")
            return True
            
        except HttpError as error:
            logger.error(f"Error logging to Google Sheets: {error}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging to Google Sheets: {e}")
            return False
    
    def create_spreadsheet(self, title: str = "GeoPolygon API Logs") -> Optional[str]:
        """
        Создает новую Google таблицу
        
        Args:
            title: название таблицы
            
        Returns:
            ID созданной таблицы
        """
        if not self.service:
            logger.warning("Google Sheets service not available")
            return None
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'API Logs',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 5
                            }
                        }
                    }
                ]
            }
            
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            
            # Добавляем заголовки
            headers = [['Дата и время', 'Широта', 'Долгота', 'Радиус (м)', 'Площадь (м²)']]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1:E1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
            logger.info(f"Created Google Spreadsheet: {spreadsheet_id}")
            return spreadsheet_id
            
        except HttpError as error:
            logger.error(f"Error creating Google Spreadsheet: {error}")
            return None
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """
        Возвращает URL таблицы для просмотра
        
        Returns:
            URL таблицы или None
        """
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        return None 