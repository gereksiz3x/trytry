import requests
import re
import sys

# Renkli çıktı
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_status(message, status="info"):
    icons = {"success": "✓", "error": "✗", "warning": "!", "info": "*"}
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    print(f"{colors.get(status, BLUE)}{icons.get(status, '*')}{RESET} {message}")

def find_active_streams():
    """Sitedeki aktif streamleri bul"""
    print_status("Site analiz ediliyor...")
    
    base_url = "https://golvar2693.sbs/"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': base_url
    })
    
    try:
        # Ana sayfayı al
        response = session.get(base_url, timeout=10)
        html_content = response.text
        
        # JavaScript dosyalarında stream URL'lerini ara
        js_pattern = r'<script[^>]+src="([^">]+\.js)"'
        js_files = re.findall(js_pattern, html_content)
        
        stream_urls = set()
        
        # Ana sayfadaki olası stream URL'lerini ara
        patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'file["\']?\s*[:=]\s*["\']([^"\']+\.m3u8)["\']',
            r'source["\']?\s*[:=]\s*["\']([^"\']+\.m3u8)["\']',
            r'streamUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and '.m3u8' in match:
                    if not match.startswith('http'):
                        match = base_url + match.lstrip('/')
                    stream_urls.add(match)
        
        # JavaScript dosyalarını tara
        for js_file in js_files[:3]:  # İlk 3 JS dosyasını tara
            try:
                if not js_file.startswith('http'):
                    js_file = base_url + js_file.lstrip('/')
                
                js_response = session.get(js_file, timeout=8)
                js_content = js_response.text
                
                for pattern in patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        if match and '.m3u8' in match:
                            if not match.startswith('http'):
                                match = base_url + match.lstrip('/')
                            stream_urls.add(match)
                            
            except:
                continue
        
        # Test edilmiş gerçek stream URL'leri
        tested_urls = [
            "https://golvar2693.sbs/hls/stream.m3u8",
            "https://golvar2693.sbs/live/stream.m3u8",
            "https://golvar2693.sbs/stream/playlist.m3u8",
            "https://golvar2693.sbs/tv/live.m3u8",
            "https://golvar2693.sbs/channels/stream.m3u8",
        ]
        
        for url in tested_urls:
            stream_urls.add(url)
        
        return list(stream_urls)
        
    except Exception as e:
        print_status(f"Analiz hatası: {e}", "error")
        return []

def test_stream_url(url, session):
    """Stream URL'sini test et"""
    try:
        response = session.head(url, timeout=8, allow_redirects=True)
        if response.status_code == 200:
            # Content-Type kontrolü
            content_type = response.headers.get('content-type', '').lower()
            if 'video' in content_type or 'application' in content_type or 'm3u8' in content_type:
                return True
            # M3U8 içeriği kontrolü
            try:
                content_response = session.get(url, timeout=5)
                if '#EXTM3U' in content_response.text:
                    return True
            except:
                pass
        return False
    except:
        return False

def create_m3u_playlist(stream_urls):
    """M3U playlist oluştur"""
    lines = ["#EXTM3U"]
    
    for i, url in enumerate(stream_urls, 1):
        channel_name = f"Golvar2693 Yayın {i}"
        lines.append(f'#EXTINF:-1 tvg-id="",{channel_name}')
        lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
        lines.append(url)
    
    return "\n".join(lines)

def main():
    print(f"{BLUE}╔══════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║           GOLVAR2693 STREAM SCANNER      ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════╝{RESET}")
    
    # Stream URL'lerini bul
    all_stream_urls = find_active_streams()
    
    if not all_stream_urls:
        print_status("Hiç stream URL'si bulunamadı", "error")
        return False
    
    print_status(f"{len(all_stream_urls)} aday stream URL'si bulundu", "info")
    
    # Stream'leri test et
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://golvar2693.sbs/'
    })
    
    working_urls = []
    
    for url in all_stream_urls:
        print_status(f"Test ediliyor: {url}", "info")
        if test_stream_url(url, session):
            print_status(f"ÇALIŞIYOR: {url}", "success")
            working_urls.append(url)
        else:
            print_status(f"Çalışmıyor: {url}", "warning")
    
    if not working_urls:
        print_status("Hiçbir stream URL'si çalışmıyor", "error")
        return False
    
    # M3U oluştur
    m3u_content = create_m3u_playlist(working_urls)
    
    try:
        with open("golvar2693.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print_status(f"M3U dosyası oluşturuldu: golvar2693.m3u", "success")
        print_status(f"Çalışan stream sayısı: {len(working_urls)}", "success")
        return True
    except Exception as e:
        print_status(f"Dosya yazma hatası: {e}", "error")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
