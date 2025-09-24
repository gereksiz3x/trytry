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
            
            # Rojadirecta'nın yapısına göre maçları bul
            # Önce tüm linkleri kontrol et
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                link_text = link.get_text(strip=True)
                link_href = link.get('href', '')
                
                # Maç içeren linkleri filtrele
                if self._is_match_link(link_text, link_href):
                    match_data = self._parse_match_link(link, link_text, link_href)
                    if match_data:
                        matches.append(match_data)
            
            # Benzersiz maçlar
            unique_matches = []
            seen_matches = set()
            for match in matches:
                match_id = f"{match['name']}_{match['time']}"
                if match_id not in seen_matches:
                    unique_matches.append(match)
                    seen_matches.add(match_id)
            
            logger.info(f"{len(unique_matches)} maç bulundu")
            return unique_matches[:10]  # İlk 10 maç
            
        except Exception as e:
            logger.error(f"Maçlar çekilirken hata: {str(e)}")
            return []
    
    def _is_match_link(self, text: str, href: str) -> bool:
        """Linkin maç linki olup olmadığını kontrol eder"""
        if not text or len(text) < 5:
            return False
        
        # Maç belirteçleri
        match_indicators = ['vs', 'vs.', ' - ', 'livestream', 'stream', 'canlı', 'yayın']
        league_indicators = ['süper lig', 'premier league', 'la liga', 'serie a', 'bundesliga', 'ligue 1']
        
        text_lower = text.lower()
        href_lower = href.lower()
        
        # vs içeren veya lig isimleri geçen linkler
        has_vs = any(indicator in text_lower for indicator in match_indicators)
        has_league = any(league in text_lower for league in league_indicators)
        has_stream = 'stream' in href_lower or 'live' in href_lower
        
        return has_vs or has_league or has_stream
    
    def _parse_match_link(self, link, text: str, href: str) -> Optional[Dict]:
        """Maç linkini parse eder"""
        try:
            # URL'yi tamamla
            if href and not href.startswith('http'):
                href = self.base_url + href if href.startswith('/') else f"{self.base_url}/{href}"
            
            # Maç saatini bul
            time_pattern = r'\d{1,2}:\d{2}'
            time_match = re.search(time_pattern, text)
            match_time = time_match.group() if time_match else "TBA"
            
            # Takım isimlerini ayıkla
            teams = self._extract_teams(text)
            
            return {
                'name': text,
                'url': href,
                'time': match_time,
                'teams': teams,
                'league': self._detect_league(text),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Maç parse edilirken hata: {str(e)}")
            return None
    
    def _extract_teams(self, text: str) -> Dict:
        """Takım isimlerini çıkarır"""
        try:
            # vs, - gibi ayırıcılara göre böl
            separators = [' vs ', ' vs. ', ' - ', ' @ ']
            for sep in separators:
                if sep in text:
                    parts = text.split(sep, 1)
                    if len(parts) == 2:
                        return {'home': parts[0].strip(), 'away': parts[1].strip()}
            
            return {'home': 'Team A', 'away': 'Team B'}
        except:
            return {'home': 'Team A', 'away': 'Team B'}
    
    def _detect_league(self, match_name: str) -> str:
        """Maçın hangi ligde olduğunu tespit eder"""
        leagues = {
            'SÜPER LİG': ['süper lig', 'super lig', 'superlig'],
            'PREMIER LEAGUE': ['premier league', 'premier'],
            'LA LIGA': ['la liga', 'laliga'],
            'SERIE A': ['serie a', 'seriea'],
            'BUNDESLIGA': ['bundesliga'],
            'LIGUE 1': ['ligue 1', 'ligue1'],
            'CHAMPIONS LEAGUE': ['champions league', 'ucl'],
            'EUROPA LEAGUE': ['europa league', 'uel']
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
            response = self.session.get(match_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stream_links = []
            
            # Tüm linkleri kontrol et
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                stream_url = link.get('href')
                stream_name = link.get_text(strip=True)
                
                if stream_url and self._is_valid_stream_url(stream_url, stream_name):
                    stream_links.append({
                        'name': stream_name or 'Unknown Stream',
                        'url': stream_url,
                        'quality': self._detect_quality(stream_name),
                        'language': self._detect_language(stream_name)
                    })
            
            # Benzersiz linkler
            unique_links = []
            seen_urls = set()
            for link in stream_links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            logger.info(f"{len(unique_links)} yayın linki bulundu")
            return unique_links[:5]  # İlk 5 link
            
        except Exception as e:
            logger.error(f"Yayın linkleri çekilirken hata: {str(e)}")
            return []
    
    def _is_valid_stream_url(self, url: str, name: str) -> bool:
        """Geçerli bir stream URL'si mi kontrol eder"""
        if not url.startswith('http'):
            return False
        
        invalid_patterns = [
            'facebook', 'twitter', 'instagram', 'telegram',
            'mailto:', 'tel:', 'javascript:',
            '.pdf', '.doc', '.xls', '.zip', '.rar'
        ]
        
        name_lower = (name or '').lower()
        url_lower = url.lower()
        
        # Spesifik stream platformları
        valid_platforms = [
            'youtube', 'twitch', 'dailymotion', 'vimeo',
            'streamable', 'stream', 'live', 'm3u8', 'hls'
        ]
        
        has_valid_platform = any(platform in url_lower for platform in valid_platforms)
        has_invalid = any(pattern in url_lower for pattern in invalid_patterns)
        
        return has_valid_platform and not has_invalid
    
    def _detect_quality(self, stream_name: str) -> str:
        """Yayın kalitesini tespit eder"""
        quality_patterns = {
            'HD': [r'\bhd\b', r'high definition', r'1080p', r'720p'],
            'SD': [r'\bsd\b', r'standard', r'480p', r'360p'],
            '4K': [r'4k', r'ultra hd', r'2160p']
        }
        
        stream_name_lower = (stream_name or '').lower()
        for quality, patterns in quality_patterns.items():
            if any(re.search(pattern, stream_name_lower) for pattern in patterns):
                return quality
        
        return 'Unknown'
    
    def _detect_language(self, stream_name: str) -> str:
        """Yayın dilini tespit eder"""
        languages = {
            'Türkçe': ['türkçe', 'turkish', 'tr', 'turkey'],
            'İngilizce': ['ingilizce', 'english', 'en', 'eng'],
            'İspanyolca': ['ispanyolca', 'spanish', 'es', 'esp'],
            'Arapça': ['arapça', 'arabic', 'ar']
        }
        
        stream_name_lower = (stream_name or '').lower()
        for lang, keywords in languages.items():
            if any(keyword in stream_name_lower for keyword in keywords):
                return lang
        
        return 'Unknown'

class M3UGenerator:
    """M3U playlist generator"""
    
    @staticmethod
    def generate_m3u_content(matches_data: Dict) -> str:
        """M3U playlist içeriği oluşturur"""
        m3u_content = ['#EXTM3U']
        
        for match_name, data in matches_data.items():
            match_info = data['match_info']
            streams = data['streams']
            
            for i, stream in enumerate(streams, 1):
                # EXTINF satırı
                duration = 180  # 3 saat
                title = f"{match_info['teams']['home']} vs {match_info['teams']['away']} - {stream['quality']}"
                if stream['language'] != 'Unknown':
                    title += f" [{stream['language']}]"
                
                extinf_line = f'#EXTINF:{duration},{title}'
                m3u_content.append(extinf_line)
                
                # Stream URL satırı
                m3u_content.append(stream['url'])
        
        return '\n'.join(m3u_content)
    
    @staticmethod
    def save_m3u_file(content: str, filename: str = 'streams.m3u'):
        """M3U dosyasını kaydeder"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"M3U dosyası kaydedildi: {filename}")
            return True
        except Exception as e:
            logger.error(f"M3U dosyası kaydedilirken hata: {str(e)}")
            return False

class StreamManager:
    def __init__(self):
        self.scraper = RojadirectaScraper()
        self.m3u_generator = M3UGenerator()
        self.data_file = 'streams_data.json'
        self.m3u_file = 'streams.m3u'
    
    def get_daily_streams(self) -> Dict:
        """Günlük maç ve yayın bilgilerini getirir"""
        matches = self.scraper.get_daily_matches()
        results = {}
        
        for i, match in enumerate(matches):
            logger.info(f"Maç {i+1}/{len(matches)}: {match['name']}")
            stream_links = self.scraper.get_stream_links(match['url'])
            
            if stream_links:
                results[match['name']] = {
                    'match_info': match,
                    'streams': stream_links,
                    'last_updated': datetime.now().isoformat()
                }
            
            time.sleep(1)  # Rate limiting
        
        # JSON ve M3U dosyalarını kaydet
        self._save_json_data(results)
        self._save_m3u_data(results)
        
        return results
    
    def _save_json_data(self, data: Dict):
        """Veriyi JSON dosyasına kaydeder"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("JSON verisi kaydedildi")
        except Exception as e:
            logger.error(f"JSON kaydedilirken hata: {str(e)}")
    
    def _save_m3u_data(self, data: Dict):
        """Veriyi M3U dosyasına kaydeder"""
        try:
            m3u_content = self.m3u_generator.generate_m3u_content(data)
            self.m3u_generator.save_m3u_file(m3u_content, self.m3u_file)
            logger.info("M3U playlist oluşturuldu")
        except Exception as e:
            logger.error(f"M3U oluşturulurken hata: {str(e)}")

def main():
    """Ana çalıştırma fonksiyonu"""
    manager = StreamManager()
    
    print("🚀 Rojadirecta M3U Stream Scraper Başlatılıyor...")
    print("=" * 50)
    
    try:
        results = manager.get_daily_streams()
        
        print(f"\n📊 Toplam {len(results)} maç bulundu:")
        print("=" * 50)
        
        total_streams = 0
        for match_name, data in results.items():
            streams_count = len(data['streams'])
            total_streams += streams_count
            print(f"\n⚽ {match_name}")
            print(f"🕒 Saat: {data['match_info']['time']}")
            print(f"📺 Yayın Sayısı: {streams_count}")
            
            for stream in data['streams'][:2]:  # İlk 2 yayın
                print(f"   🔗 {stream['name']} - {stream['quality']}")
        
        print(f"\n📈 Toplam {total_streams} yayın linki bulundu")
        print(f"💾 JSON dosyası: 'streams_data.json'")
        print(f"📺 M3U Playlist: 'streams.m3u'")
        print(f"\n✅ İşlem tamamlandı!")
        
    except Exception as e:
        logger.error(f"Ana fonksiyonda hata: {str(e)}")
        print("❌ Bir hata oluştu, detaylar için logları kontrol edin")

if __name__ == "__main__":
    main()
