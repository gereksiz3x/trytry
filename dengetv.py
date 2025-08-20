#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import sys
import time
from urllib.parse import urljoin

# Terminal renkleri
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Kullanıcı ajanı
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# DengeTV kanal listesi (sitedeki sıraya göre)
KANALLAR = [
    {"dosya": "yayin1.m3u8", "tvg_id": "BEINSPORTS1", "kanal_adi": "BEIN SPORTS 1"},
    {"dosya": "yayin2.m3u8", "tvg_id": "BEINSPORTS2", "kanal_adi": "BEIN SPORTS 2"},
    {"dosya": "yayin3.m3u8", "tvg_id": "BEINSPORTS3", "kanal_adi": "BEIN SPORTS 3"},
    {"dosya": "yayin4.m3u8", "tvg_id": "BEINSPORTS4", "kanal_adi": "BEIN SPORTS 4"},
    {"dosya": "yayin5.m3u8", "tvg_id": "BEINSPORTS5", "kanal_adi": "BEIN SPORTS 5"},
    {"dosya": "yayin6.m3u8", "tvg_id": "BEINSPORTSMAX1", "kanal_adi": "BEIN SPORTS MAX 1"},
    {"dosya": "yayin7.m3u8", "tvg_id": "BEINSPORTSMAX2", "kanal_adi": "BEIN SPORTS MAX 2"},
    {"dosya": "yayin8.m3u8", "tvg_id": "SSPORT1", "kanal_adi": "S-SPORT 1"},
    {"dosya": "yayin9.m3u8", "tvg_id": "SSPORT2", "kanal_adi": "S-SPORT 2"},
    {"dosya": "yayin10.m3u8", "tvg_id": "SSPORT+", "kanal_adi": "S-SPORT +"},
    {"dosya": "yayin11.m3u8", "tvg_id": "TIVIBUSPOR1", "kanal_adi": "TIVIBU SPOR 1"},
    {"dosya": "yayin12.m3u8", "tvg_id": "TIVIBUSPOR2", "kanal_adi": "TIVIBU SPOR 2"},
    {"dosya": "yayin13.m3u8", "tvg_id": "TIVIBUSPOR3", "kanal_adi": "TIVIBU SPOR 3"},
    {"dosya": "yayin14.m3u8", "tvg_id": "SMARTSPOR1", "kanal_adi": "SMART SPOR 1"},
    {"dosya": "yayin15.m3u8", "tvg_id": "SMARTSPOR2", "kanal_adi": "SMART SPOR 2"},
    {"dosya": "yayin16.m3u8", "tvg_id": "TRTSPOR", "kanal_adi": "TRT SPOR"},
    {"dosya": "yayin17.m3u8", "tvg_id": "TRTSPORYILDIZ", "kanal_adi": "TRT SPOR YILDIZ"},
    {"dosya": "yayin18.m3u8", "tvg_id": "ASPOR", "kanal_adi": "A SPOR"},
    {"dosya": "yayin19.m3u8", "tvg_id": "ATV", "kanal_adi": "ATV"},
    {"dosya": "yayin20.m3u8", "tvg_id": "TV8", "kanal_adi": "TV8"},
    {"dosya": "yayin21.m3u8", "tvg_id": "TV85", "kanal_adi": "TV8.5"},
    {"dosya": "yayin22.m3u8", "tvg_id": "NBATV", "kanal_adi": "NBA TV"},
    {"dosya": "yayin23.m3u8", "tvg_id": "EXXENSPOR1", "kanal_adi": "EXXEN SPOR 1"},
    {"dosya": "yayin24.m3u8", "tvg_id": "EXXENSPOR2", "kanal_adi": "EXXEN SPOR 2"},
    {"dosya": "yayin25.m3u8", "tvg_id": "EXXENSPOR3", "kanal_adi": "EXXEN SPOR 3"},
    {"dosya": "yayin26.m3u8", "tvg_id": "EXXENSPOR4", "kanal_adi": "EXXEN SPOR 4"},
    {"dosya": "yayin27.m3u8", "tvg_id": "EXXENSPOR5", "kanal_adi": "EXXEN SPOR 5"},
    {"dosya": "yayin28.m3u8", "tvg_id": "EXXENSPOR6", "kanal_adi": "EXXEN SPOR 6"},
    {"dosya": "yayin29.m3u8", "tvg_id": "EXXENSPOR7", "kanal_adi": "EXXEN SPOR 7"},
    {"dosya": "yayin30.m3u8", "tvg_id": "EXXENSPOR8", "kanal_adi": "EXXEN SPOR 8"},
]

def get_base_url(site_url):
    """Siteyi kontrol edip base URL'yi bulur"""
    print(f"{GREEN}[*] Site kontrol ediliyor: {site_url}{RESET}")
    
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(site_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # JavaScript dosyalarında base URL'yi ara
        js_patterns = [
            r'baseurl\s*[:=]\s*["\']([^"\']+)["\']',
            r'source\s*[:=]\s*["\']([^"\']+\.m3u8)["\']',
            r'player\.setup\([^)]*src["\']\s*[:,]\s*["\']([^"\']+)["\']',
            r'file["\']\s*[:,]\s*["\']([^"\']+\.m3u8)["\']'
        ]
        
        for pattern in js_patterns:
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                base_url = match.group(1)
                # Eğer base URL göreceli ise, site URL'si ile birleştir
                if base_url.startswith('/'):
                    base_url = urljoin(site_url, base_url)
                # m3u8 dosyasının bulunduğu dizini al
                if base_url.endswith('.m3u8'):
                    base_url = base_url.rsplit('/', 1)[0] + '/'
                print(f"{GREEN}[+] Base URL bulundu: {base_url}{RESET}")
                return base_url
        
        # Eğer JavaScript pattern'leri ile bulunamazsa, HTML içinde ara
        html_patterns = [
            r'<source[^>]+src=["\']([^"\']+\.m3u8)["\']',
            r'videojs[^>]+src=["\']([^"\']+\.m3u8)["\']',
            r'data-source=["\']([^"\']+\.m3u8)["\']'
        ]
        
        for pattern in html_patterns:
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                base_url = match.group(1)
                if base_url.startswith('/'):
                    base_url = urljoin(site_url, base_url)
                if base_url.endswith('.m3u8'):
                    base_url = base_url.rsplit('/', 1)[0] + '/'
                print(f"{GREEN}[+] Base URL bulundu: {base_url}{RESET}")
                return base_url
        
        print(f"{YELLOW}[-] Base URL bulunamadı, varsayılan yol deneniyor...{RESET}")
        # Varsayılan yol olarak site URL'sini kullan
        return site_url.rstrip('/') + '/'
        
    except requests.RequestException as e:
        print(f"{RED}[-] Siteye erişilemedi: {e}{RESET}")
        return None

def test_stream_url(stream_url, referer):
    """Stream URL'sini test eder"""
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Referer': referer,
            'Accept': '*/*',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Origin': referer,
            'Connection': 'keep-alive',
        }
        
        response = requests.head(stream_url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return True
        
        # HEAD isteği başarısız olursa GET dene (bazı sunucular HEAD'i reddedebilir)
        response = requests.get(stream_url, headers=headers, timeout=5, stream=True)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def generate_m3u(base_url, site_url, output_file="dengetv.m3u"):
    """M3U playlist oluşturur"""
    print(f"{GREEN}[*] M3U playlist oluşturuluyor...{RESET}")
    
    lines = ["#EXTM3U"]
    active_channels = 0
    
    for idx, channel in enumerate(KANALLAR, start=1):
        stream_url = base_url.rstrip('/') + '/' + channel["dosya"]
        
        # Stream URL'sini test et
        if test_stream_url(stream_url, site_url):
            status = f"{GREEN}✓{RESET}"
            active_channels += 1
            
            # EXTINF satırı
            lines.append(f'#EXTINF:-1 tvg-id="{channel["tvg_id"]}" tvg-name="{channel["kanal_adi"]}" tvg-logo="",{channel["kanal_adi"]}')
            
            # VLCOPT satırları
            lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
            lines.append(f'#EXTVLCOPT:http-referrer={site_url}')
            
            # Stream URL'si
            lines.append(stream_url)
        else:
            status = f"{RED}✗{RESET}"
        
        print(f"  {status} {idx:02d}. {channel['kanal_adi']}")
    
    # Playlist'i dosyaya yaz
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"{GREEN}[+] Playlist oluşturuldu: {output_file}{RESET}")
    print(f"{GREEN}[+] Aktif kanal sayısı: {active_channels}/{len(KANALLAR)}{RESET}")
    
    return active_channels

def main():
    print(f"{BLUE}=== DengeTV M3U Playlist Oluşturucu ==={RESET}")
    
    site_url = "https://dengetv54.live/"
    
    # Base URL'yi al
    base_url = get_base_url(site_url)
    if not base_url:
        print(f"{RED}[!] Base URL alınamadı. Script sonlandırılıyor.{RESET}")
        sys.exit(1)
    
    # M3U playlist oluştur
    active_channels = generate_m3u(base_url, site_url)
    
    if active_channels == 0:
        print(f"{YELLOW}[!] Hiçbir kanal bulunamadı. Site yapısı değişmiş olabilir.{RESET}")
    else:
        print(f"{GREEN}[+] İşlem başarıyla tamamlandı!{RESET}")

if __name__ == "__main__":
    main()
