import requests
import re
import sys
import json
from urllib.parse import urljoin, quote
from datetime import datetime

# ========= RENK TANIMLARI =========
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"

# ========= YARDIMCI FONKSİYONLAR =========
def print_status(message, status="info"):
    """Renkli durum mesajı yazdır"""
    if status == "success":
        print(f"{GREEN}[✓]{RESET} {message}")
    elif status == "error":
        print(f"{RED}[✗]{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}[!]{RESET} {message}")
    else:
        print(f"{BLUE}[*]{RESET} {message}")

def get_site_content(url):
    """Site içeriğini al"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
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
    """HTML içeriğinden maç bilgilerini çıkar"""
    matches = []
    
    # Maç pattern'leri - daha esnek yapı
    match_patterns = [
        r'<a[^>]*href="([^"]*mac[^"]*)"[^>]*>(.*?)</a>',
        r'<div[^>]*class="[^"]*match[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r'data-url="([^"]*)"[^>]*data-title="([^"]*)"',
        r'<li[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</li>',
    ]
    
    for pattern in match_patterns:
        found_matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match_url, match_title in found_matches:
            if 'mac' in match_url.lower() and match_title.strip():
                if not match_url.startswith('http'):
                    match_url = urljoin(base_url, match_url)
                
                # Title temizleme
                title = re.sub(r'<[^>]*>', '', match_title).strip()
                if title and len(title) > 5:  # Anlamlı bir başlık olduğundan emin ol
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
        
        # Çeşitli stream URL pattern'leri
        patterns = [
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
            r'file["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'source["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'src["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'player\.setup\([^)]*file["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'hlsUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'videoUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'streamUrl["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for stream_url in matches:
                if stream_url and '.m3u8' in stream_url:
                    # URL'yi temizle
                    stream_url = re.sub(r'[\\"\'\)\;]', '', stream_url)
                    if not stream_url.startswith('http'):
                        stream_url = urljoin(match_url, stream_url)
                    return stream_url
        
        return None
        
    except Exception as e:
        print_status(f"Stream çıkarılırken hata: {e}", "error")
        return None

def get_direct_stream_urls():
    """Direkt olarak bilinen stream URL'lerini dene"""
    direct_urls = [
        "https://golvar2693.sbs/stream/live1.m3u8",
        "https://golvar2693.sbs/stream/sport1.m3u8",
        "https://golvar2693.sbs/stream/tv1.m3u8",
        "https://golvar2693.sbs/live/stream.m3u8",
        "https://golvar2693.sbs/hls/stream.m3u8",
    ]
    
    for url in direct_urls:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return url
        except:
            continue
    
    return None

def generate_m3u_playlist(matches):
    """M3U playlist oluştur"""
    if not matches:
        return None
    
    lines = ["#EXTM3U"]
    valid_channels = 0
    
    for idx, match in enumerate(matches, 1):
        stream_url = extract_stream_from_match_page(match['url'])
        
        if not stream_url:
            # Alternatif olarak direkt URL'leri dene
            stream_url = get_direct_stream_urls()
        
        if stream_url:
            channel_name = f"⚽ {match['title']}"
            
            lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name}",{channel_name}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
            lines.append(stream_url)
            
            print_status(f"{idx:02d}. {channel_name}", "success")
            valid_channels += 1
        else:
            print_status(f"{idx:02d}. {match['title']} (Stream bulunamadı)", "warning")
    
    return "\n".join(lines), valid_channels

def main():
    """Ana fonksiyon"""
    print(f"{CYAN}{BOLD}╔══════════════════════════════════════════╗")
    print(f"║           Golvar2693 Maç Scanner          ║")
    print(f"╚══════════════════════════════════════════╝{RESET}\n")
    
    base_url = "https://golvar2693.sbs/"
    
    # Ana sayfayı al
    print_status("Ana sayfa yükleniyor...")
    html_content = get_site_content(base_url)
    if not html_content:
        print_status("Alternatif tarama yöntemleri deneniyor...", "warning")
        # Direkt maç URL'lerini deneyelim
        html_content = ""
    
    # Maçları çıkar
    print_status("Maçlar taranıyor...")
    matches = extract_matches_from_html(html_content, base_url)
    
    if not matches:
        print_status("Otomatik maç bulunamadı, manuel URL'ler deneniyor...", "warning")
        
        # Manuel olarak bilinen maç URL'lerini oluştur
        matches = [
            {
                'url': base_url + 'mac/letonya-sirbistan-cbc-sport/',
                'title': 'Letonya - Sırbistan (CBC Sport)',
                'type': 'live_match'
            },
            {
                'url': base_url + 'mac/live-stream-1/',
                'title': 'Canlı Maç 1',
                'type': 'live_match'
            },
            {
                'url': base_url + 'mac/live-stream-2/',
                'title': 'Canlı Maç 2', 
                'type': 'live_match'
            }
        ]
    
    print_status(f"{len(matches)} maç bulundu", "success")
    
    # M3U playlist oluştur
    print_status("Stream URL'leri çıkarılıyor...")
    playlist, valid_count = generate_m3u_playlist(matches)
    
    if not playlist or valid_count == 0:
        print_status("Hiçbir maç için stream bulunamadı!", "error")
        
        # Son çare: Sabit stream URL'leri
        print_status("Sabit stream URL'leri deneniyor...", "warning")
        fixed_streams = [
            "https://golvar2693.sbs/hls/stream.m3u8",
            "https://golvar2693.sbs/live/tv.m3u8", 
            "https://golvar2693.sbs/stream/channel1.m3u8"
        ]
        
        lines = ["#EXTM3U"]
        valid_count = 0
        for idx, stream_url in enumerate(fixed_streams, 1):
            try:
                response = requests.head(stream_url, timeout=5)
                if response.status_code == 200:
                    lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="Golvar2693 Stream {idx}",Golvar2693 Stream {idx}')
                    lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
                    lines.append(stream_url)
                    print_status(f"{idx:02d}. Golvar2693 Stream {idx}", "success")
                    valid_count += 1
            except:
                continue
        
        playlist = "\n".join(lines) if valid_count > 0 else None
    
    if not playlist or valid_count == 0:
        print_status("Hiçbir stream bulunamadı!", "error")
        sys.exit(1)
    
    # Dosyaya yaz
    filename = "golvar2693.m3u"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(playlist)
        print_status(f"Playlist oluşturuldu: {filename}", "success")
        print_status(f"Aktif stream sayısı: {valid_count}", "success")
        
    except Exception as e:
        print_status(f"Dosya yazılırken hata: {e}", "error")
        sys.exit(1)
    
    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════╗")
    print(f"║            İŞLEM TAMAMLANDI              ║")
    print(f"║   Aktif Stream: {valid_count:2d}                       ║")
    print(f"╚══════════════════════════════════════════╝{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}[!] İşlem kullanıcı tarafından durduruldu.{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{RED}[!] Beklenmeyen hata: {e}{RESET}")
        sys.exit(1)
