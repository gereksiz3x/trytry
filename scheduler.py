import schedule
import time
from main import StreamManager
import logging

logger = logging.getLogger(__name__)

def scheduled_job():
    """Zamanlanmış görev"""
    logger.info("Zamanlanmış görev çalıştırılıyor...")
    manager = StreamManager()
    manager.get_daily_streams()

# Görevleri planla
schedule.every().day.at("09:00").do(scheduled_job)  # Sabah 9
schedule.every().day.at("15:00").do(scheduled_job)  # Öğlen 3
schedule.every().day.at("19:00").do(scheduled_job)  # Akşam 7

if __name__ == "__main__":
    print("⏰ Scheduler başlatıldı...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1 dakika bekle