import os
import re
import logging
from httpx import Client

class XYZsportsManager:
    def __init__(self, cikti_dosyasi):
        self.cikti_dosyasi = cikti_dosyasi
        self.httpx = Client(timeout=10, verify=os.getenv("DISABLE_SSL_VERIFY", "False") == "False")
        self.channel_ids = ["Manoto-TV", "BBC-Persian", "VOA-PNN"]
        logging.basicConfig(level=logging.INFO)

    def find_working_domain(self):
        domains = ["https://www.parsatv.com/m/", "https://backup.example.com"]
        for url in domains:
            try:
                r = self.httpx.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and "uxsyplayer" in r.text:
                    return r.text, url
            except Exception as e:
                logging.warning(f"{url} erişilemedi: {str(e)}")
        return None, None

    # Diğer fonksiyonlar aynı kalabilir...

if __name__ == "__main__":
    try:
        XYZsportsManager("Umitmod.m3u").calistir()
    except Exception as e:
        logging.error(f"Script hatası: {str(e)}")
        exit(1)
