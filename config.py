import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Site ayarları
    BASE_URL = "https://www.rojadirectaenvivo.pl"
    
    # Request ayarları
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    DELAY_BETWEEN_REQUESTS = 2
    
    # Dosya ayarları
    DATA_FILE = "streams_data.json"
    LOG_FILE = "scraper.log"
    
    # GitHub Actions ayarları
    UPDATE_INTERVAL_HOURS = 6