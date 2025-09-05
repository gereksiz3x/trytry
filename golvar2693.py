import requests
import re
import sys
from urllib.parse import urljoin, quote
import json

# Renkli çıktı
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

def print_status(message, status="info"):
    icons = {"success": "✓", "error": "✗", "warning": "!", "info": "*"}
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    print(f"{colors.get(status, BLUE)}{icons.get(status, '*')}{RESET} {message}")

def get_site_content(url):
    """Site içeriğini al"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print_status(f"Siteye erişilemedi: {e}", "error")
        return None

def extract_matches_from_html(html_content, base_url):
    """HTML içeriğinden maçları ve yayınları çıkar"""
    matches = []
    
    # Maç listesi pattern'leri - daha kapsamlı
    match_patterns = [
        r'<a[^>]*href="(/mac/[^"]*)"[^>]*>(.*?)</a>',
        r'<div[^>]*class="[^"]*match-item[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r'<li[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</li>',
        r'data-url="([^"]*)"[^>]*data-title="([^"]*)"',
        r'<div[^>]*class="[^"]*live-match[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
    ]
    
    for pattern in match_patterns:
        found_matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match_url, match_title in found_matches:
            if 'mac' in match_url.lower() and match_title.strip():
                # URL'yi tamamla
                if not match_url.startswith('http'):
                    match_url = urljoin(base_url, match_url)
                
                # Başlığı temizle
                title = re.sub(r'<[^>]*>', '', match_title).strip()
                title = re.sub(r'\s+', ' ', title)  # Fazla boşlukları temizle
                
                if title and len(title) > 3:  # Anlamlı başlık kontrolü
                    matches.append({
                        'url': match_url,
                        'title': title,
                        'type': 'live_match'
                    })
    
    return matches

def extract_stream_from_match_page(match_url):
    """Maç sayfasından stream URL'sini çıkar"""
    try:
        content = get_site_content(match_url)
        if not content:
            return None
        
        # Çeşitli stream pattern'leri
        patterns = [
            r'file["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'source["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'src["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'player\.setup\([^)]*file["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'hlsUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'streamUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'videoUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',  # Direkt URL
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for stream_url in matches:
                if stream_url and '.m3u8' in stream_url:
                    # URL'yi temizle ve tamamla
                    stream_url = re.sub(r'[\\"\'\)\;]', '', stream_url)
                    if not stream_url.startswith('http'):
                        stream_url = urljoin(match_url, stream_url)
                    
                    # Stream'i test et
                    if test_stream(stream_url):
                        return stream_url
        
        return None
        
    except Exception as e:
        print_status(f"Stream çıkarılırken hata: {e}", "error")
        return None

def test_stream(stream_url):
    """Stream URL'sini test et"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://golvar2693.sbs/',
            'Accept': '*/*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # HEAD isteği ile hızlı kontrol
        response = requests.head(stream_url, headers=headers, timeout=8, allow_redirects=True)
        if response.status_code == 200:
            return True
            
        # GET isteği ile içerik kontrolü
        response = requests.get(stream_url, headers=headers, timeout=10)
        if response.status_code == 200 and ('#EXTM3U' in response.text or 'video' in response.headers.get('content-type', '')):
            return True
            
        return False
        
    except:
        return False

def generate_m3u_playlist(matches_with_streams):
    """M3U playlist oluştur"""
    lines = ["#EXTM3U"]
    
    for idx, match in enumerate(matches_with_streams, 1):
        channel_name = f"⚽ {match['title']}"
        lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name}",{channel_name}')
        lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
        lines.append(match['stream_url'])
    
    return "\n".join(lines)

def main():
    print(f"{CYAN}{BOLD}╔══════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║        GOLVAR2693 MAÇ TARAYICI           ║{RESET}")
    print(f"{CYAN}{BOLD}╚══════════════════════════════════════════╝{RESET}")
    
    base_url = "https://golvar2693.sbs/"
    
    # Ana sayfayı al
    print_status("Ana sayfa yükleniyor...")
    html_content = get_site_content(base_url)
    
    if not html_content:
        print_status("Siteye erişilemedi, alternatif URL'ler deneniyor...", "warning")
        # Alternatif sayfaları dene
        alternative_urls = [
            base_url + "maclar/",
            base_url + "live/",
            base_url + "canli-yayin/",
            base_url + "tum-maclar/",
        ]
        
        for alt_url in alternative_urls:
            html_content = get_site_content(alt_url)
            if html_content:
                base_url = alt_url.rsplit('/', 1)[0] + '/' if '/' in alt_url else alt_url
                break
    
    if not html_content:
        print_status("Hiçbir sayfaya erişilemedi", "error")
        sys.exit(1)
    
    # Maçları çıkar
    print_status("Maç listesi taranıyor...")
    matches = extract_matches_from_html(html_content, base_url)
    
    if not matches:
        print_status("Maç bulunamadı, manuel URL'ler deneniyor...", "warning")
        # Manuel maç URL'leri
        matches = [
            {'url': base_url + 'mac/letonya-sirbistan-cbc-sport/', 'title': 'Letonya - Sırbistan (CBC Sport)', 'type': 'live_match'},
            {'url': base_url + 'mac/canli-yayin-1/', 'title': 'Canlı Maç 1', 'type': 'live_match'},
            {'url': base_url + 'mac/canli-yayin-2/', 'title': 'Canlı Maç 2', 'type': 'live_match'},
        ]
    
    print_status(f"{len(matches)} maç bulundu", "success")
    
    # Her maç için stream ara
    matches_with_streams = []
    print_status("Stream URL'leri aranıyor...")
    
    for idx, match in enumerate(matches, 1):
        print_status(f"({idx}/{len(matches)}) {match['title']}")
        stream_url = extract_stream_from_match_page(match['url'])
        
        if stream_url:
            match['stream_url'] = stream_url
            matches_with_streams.append(match)
            print_status(f"  ✓ Stream bulundu: {stream_url}", "success")
        else:
            print_status(f"  ✗ Stream bulunamadı", "warning")
    
    if not matches_with_streams:
        print_status("Hiçbir maç için stream bulunamadı", "error")
        sys.exit(1)
    
    # M3U oluştur
    print_status("M3U playlist oluşturuluyor...")
    playlist = generate_m3u_playlist(matches_with_streams)
    
    # Dosyaya yaz
    try:
        with open("golvar2693.m3u", "w", encoding="utf-8") as f:
            f.write(playlist)
        print_status(f"golvar2693.m3u oluşturuldu", "success")
        print_status(f"{len(matches_with_streams)} maç eklendi", "success")
        
    except Exception as e:
        print_status(f"Dosya yazma hatası: {e}", "error")
        sys.exit(1)

if __name__ == "__main__":
    main()
