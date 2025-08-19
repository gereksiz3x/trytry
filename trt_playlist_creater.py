import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin, quote
import argparse
import sys

class TRTPlaylistCreator:
    def __init__(self):
        self.base_url = "https://www.canlitv.top/tr"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.channels = {
            'TRT 1': 'trt-1',
            'Show TV': 'show-tv',
            'Star TV': 'star-tv',
            'TRT Haber': 'trt-haber',
            'ATV': 'atv',
            'FOX': 'fox-tv',
            'Kanal D': 'kanal-d',
            'TV8': 'tv8',
            'TRT Spor': 'trt-spor',
            'beIN Sports': 'bein-sports'
        }
    
    def fetch_stream_url(self, channel_slug):
        """Kanalın sayfasından yayın URL'sini çeker"""
        try:
            channel_url = f"{self.base_url}/{channel_slug}"
            response = requests.get(channel_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # İframe içindeki URL'yi bulma
            iframe = soup.find('iframe', {'id': 'yayin-iframe'})
            if iframe and iframe.get('src'):
                return iframe['src']
            
            # Alternatif olarak JavaScript kodundan URL'yi çıkarma
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'player.setup' in script.string:
                    match = re.search(r"file\s*:\s*['\"]([^'\"]+)['\"]", script.string)
                    if match:
                        return match.group(1)
            
            return None
        except Exception as e:
            print(f"Hata oluştu ({channel_slug}): {str(e)}")
            return None
    
    def generate_m3u_playlist(self):
        """M3U playlist oluşturur"""
        playlist = "#EXTM3U\n"
        successful_channels = 0
        
        for name, slug in self.channels.items():
            print(f"{name} kanalı işleniyor...")
            stream_url = self.fetch_stream_url(slug)
            
            if stream_url:
                # Eğer göreceli bir URL ise tam URL'ye dönüştür
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                elif stream_url.startswith('/'):
                    stream_url = self.base_url + stream_url
                
                playlist += f'#EXTINF:-1 tvg-id="{slug}" tvg-name="{name}" group-title="TR Kanalları",{name}\n'
                playlist += f"{stream_url}\n"
                
                print(f"✓ {name} eklendi")
                successful_channels += 1
            else:
                print(f"✗ {name} için stream URL bulunamadı")
            
            # Sunucuya aşırı yük bindirmemek için bekleme
            time.sleep(1)
        
        print(f"\nToplam {successful_channels}/{len(self.channels)} kanal başarıyla eklendi.")
        return playlist
    
    def save_playlist(self, filename="trt_playlist.m3u"):
        """Playlist'i dosyaya kaydeder"""
        playlist = self.generate_m3u_playlist()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(playlist)
        
        print(f"Playlist '{filename}' dosyasına kaydedildi.")
        return playlist

def main():
    parser = argparse.ArgumentParser(description='TRT TV Kanalları M3U Playlist Oluşturucu')
    parser.add_argument('-o', '--output', default='trt_playlist.m3u', 
                       help='Çıktı dosyası adı (varsayılan: trt_playlist.m3u)')
    parser.add_argument('-q', '--quiet', action='store_true', 
                       help='Sessiz mod (sadece hata mesajları gösterilir)')
    
    args = parser.parse_args()
    
    if args.quiet:
        # Çıktıyı sessiz mod için devre dışı bırak
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    
    try:
        creator = TRTPlaylistCreator()
        playlist = creator.save_playlist(args.output)
        
        if args.quiet:
            # Sessiz modu kapat ve başarı mesajını göster
            sys.stdout = original_stdout
            print(f"Playlist başarıyla oluşturuldu: {args.output}")
            
    except Exception as e:
        if args.quiet:
            sys.stdout = original_stdout
        print(f"Bir hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()
