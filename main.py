import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime, timedelta
import os
import re
from typing import Dict, List, Optional

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RojadirectaScraper:
    def __init__(self):
        self.base_url = "https://www.rojadirectaenvivo.pl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        })
    
    def get_daily_matches(self) -> List[Dict]:
        """Günlük maç programını çeker"""
        try:
            logger.info("Günlük maçlar çekiliyor...")
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = []
            
            # Maçları bul - Rojadirecta'nın yapısına göre
            match_elements = soup.find_all('div', class_=re.compile(r'match|partido|game', re.I))
            
            # Eğer özel class yoksa, tablo veya liste elemanlarını ara
            if not match_elements:
                match_elements = soup.find_all('tr') + soup.find_all('li')
            
            for element in match_elements:
                match_text = element.get_text(strip=True)
                if any(league in match_text.upper() for league in ['SÜPER LİG', 'PREMIER LEAGUE', 'LA LIGA', 'SERIE A', 'BUNDESLIGA']):
                    match_data = self._parse_match_element(element)
                    if match_data:
                        matches.append(match_data)
            
            logger.info(f"{len(matches)} maç bulundu")
            return matches
            
        except Exception as e:
            logger.error(f"Maçlar çekilirken hata: {str(e)}")
            return []
    
    def _parse_match_element(self, element) -> Optional[Dict]:
        """Maç elementini parse eder"""
        try:
            link_element = element.find('a')
            if not link_element:
                return None
            
            match_name = link_element.get_text(strip=True)
            match_url = link_element.get('href')
            
            if match_url and not match_url.startswith('http'):
                match_url = self.base_url + match_url if match_url.startswith('/') else f"{self.base_url}/{match_url}"
            
            # Maç saatini bul
            time_pattern = r'\d{1,2}:\d{2}'
            time_match = re.search(time_pattern, element.get_text())
            match_time = time_match.group() if time_match else "Bilinmiyor"
            
            return {
                'name': match_name,
                'url': match_url,
                'time': match_time,
                'league': self._detect_league(match_name),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Maç parse edilirken hata: {str(e)}")
            return None
    
    def _detect_league(self, match_name: str) -> str:
        """Maçın hangi ligde olduğunu tespit eder"""
        leagues = {
            'SÜPER LİG': ['süper lig', 'super lig', 'superlig'],
            'PREMIER LEAGUE': ['premier league', 'premier'],
            'LA LIGA': ['la liga', 'laliga'],
            'SERIE A': ['serie a', 'seriea'],
            'BUNDESLIGA': ['bundesliga'],
            'LIGUE 1': ['ligue 1', 'ligue1']
        }
        
        match_name_upper = match_name.upper()
        for league, keywords in leagues.items():
            if any(keyword.upper() in match_name_upper for keyword in keywords):
                return league
        
        return "Diğer"
    
    def get_stream_links(self, match_url: str) -> List[Dict]:
        """Maç sayfasındaki yayın linklerini çeker"""
        try:
            logger.info(f"Yayın linkleri çekiliyor: {match_url}")
            response = self.session.get(match_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stream_links = []
            
            # Stream linklerini bul
            stream_elements = soup.find_all('a', href=re.compile(r'stream|yayın|canlı|live', re.I))
            
            for stream_element in stream_elements:
                stream_url = stream_element.get('href')
                stream_name = stream_element.get_text(strip=True)
                
                if stream_url and self._is_valid_stream_url(stream_url):
                    stream_links.append({
                        'name': stream_name or 'Bilinmeyen Yayın',
                        'url': stream_url,
                        'quality': self._detect_quality(stream_name),
                        'working': True  # Test edilecek
                    })
            
            # Benzersiz linkler
            unique_links = []
            seen_urls = set()
            for link in stream_links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            logger.info(f"{len(unique_links)} yayın linki bulundu")
            return unique_links[:10]  # İlk 10 link
            
        except Exception as e:
            logger.error(f"Yayın linkleri çekilirken hata: {str(e)}")
            return []
    
    def _is_valid_stream_url(self, url: str) -> bool:
        """Geçerli bir stream URL'si mi kontrol eder"""
        invalid_patterns = [
            r'facebook', r'twitter', r'instagram', r'telegram',
            r'mailto:', r'tel:', r'javascript:',
            r'\.pdf$', r'\.doc$', r'\.xls$'
        ]
        
        url_lower = url.lower()
        return (url.startswith('http') and 
                not any(pattern in url_lower for pattern in invalid_patterns))
    
    def _detect_quality(self, stream_name: str) -> str:
        """Yayın kalitesini tespit eder"""
        quality_patterns = {
            'HD': [r'hd', r'high definition', r'1080p', r'720p'],
            'SD': [r'sd', r'standard', r'480p', r'360p'],
            '4K': [r'4k', r'ultra hd', r'2160p']
        }
        
        stream_name_lower = stream_name.lower()
        for quality, patterns in quality_patterns.items():
            if any(re.search(pattern, stream_name_lower) for pattern in patterns):
                return quality
        
        return 'Bilinmiyor'
    
    def test_stream_link(self, stream_url: str) -> bool:
        """Yayın linkinin çalışıp çalışmadığını test eder"""
        try:
            response = self.session.head(stream_url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

class StreamManager:
    def __init__(self):
        self.scraper = RojadirectaScraper()
        self.data_file = 'streams_data.json'
    
    def get_daily_streams(self) -> Dict:
        """Günlük maç ve yayın bilgilerini getirir"""
        matches = self.scraper.get_daily_matches()
        results = {}
        
        for match in matches[:5]:  # İlk 5 maç için
            logger.info(f"Maç işleniyor: {match['name']}")
            stream_links = self.scraper.get_stream_links(match['url'])
            
            # Stream linklerini test et
            for stream_link in stream_links:
                stream_link['working'] = self.scraper.test_stream_link(stream_link['url'])
            
            results[match['name']] = {
                'match_info': match,
                'streams': stream_links,
                'last_updated': datetime.now().isoformat()
            }
            
            time.sleep(2)  # Rate limiting
        
        self._save_data(results)
        return results
    
    def _save_data(self, data: Dict):
        """Veriyi JSON dosyasına kaydeder"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Veri kaydedildi")
        except Exception as e:
            logger.error(f"Veri kaydedilirken hata: {str(e)}")

def main():
    """Ana çalıştırma fonksiyonu"""
    manager = StreamManager()
    
    print("🚀 Rojadirecta Stream Scraper Başlatılıyor...")
    print("=" * 50)
    
    try:
        results = manager.get_daily_streams()
        
        print(f"\n📊 Toplam {len(results)} maç bulundu:")
        print("=" * 50)
        
        for match_name, data in results.items():
            working_streams = [s for s in data['streams'] if s['working']]
            print(f"\n⚽ {match_name}")
            print(f"🕒 Saat: {data['match_info']['time']}")
            print(f"📺 Çalışan Yayınlar: {len(working_streams)}/{len(data['streams'])}")
            
            for stream in working_streams[:3]:  # İlk 3 çalışan yayın
                print(f"   🔗 {stream['name']} - {stream['quality']}")
        
        print(f"\n✅ Veriler '{manager.data_file}' dosyasına kaydedildi")
        
    except Exception as e:
        logger.error(f"Ana fonksiyonda hata: {str(e)}")
        print("❌ Bir hata oluştu, detaylar için logları kontrol edin")

if __name__ == "__main__":
    main()