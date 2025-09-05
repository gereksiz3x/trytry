import requests
import re
import sys
import json
from urllib.parse import urljoin

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
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print_status(f"Siteye erişilemedi: {e}", "error")
        return None

def extract_channels_from_html(html_content, base_url):
    """HTML içeriğinden kanal bilgilerini çıkar"""
    channels = []
    
    # Maç yayınlarını bul (canlı maçlar)
    match_patterns = [
        r'<div[^>]*class="[^"]*match-item[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>.*?<div[^>]*class="[^"]*match-title[^"]*"[^>]*>(.*?)</div>',
        r'data-channel="([^"]+)"[^>]*data-title="([^"]+)"',
        r'<a[^>]*href="([^"]*channel\.html[^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"',
    ]
    
    for pattern in match_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if len(match) == 3:
                channel_url, image_url, title = match
                if not channel_url.startswith('http'):
                    channel_url = urljoin(base_url, channel_url)
                channels.append({
                    'url': channel_url,
                    'title': title.strip(),
                    'type': 'live_match'
                })
    
    # Normal kanalları bul
    channel_patterns = [
        r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*channel-link[^"]*"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"',
        r'<li[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>.*?</a>.*?</li>',
    ]
    
    for pattern in channel_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if len(match) == 3:
                channel_url, image_url, title = match
                if not channel_url.startswith('http'):
                    channel_url = urljoin(base_url, channel_url)
                if 'channel' in channel_url.lower():
                    channels.append({
                        'url': channel_url,
                        'title': title.strip(),
                        'type': 'tv_channel'
                    })
    
    return channels

def extract_stream_url(channel_url):
    """Kanal sayfasından stream URL'sini çıkar"""
    try:
        content = get_site_content(channel_url)
        if not content:
            return None
        
        # Stream URL pattern'leri
        patterns = [
            r'file\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'source\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'src\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'player\.setup\([^)]*file["\']?\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'hlsUrl\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                stream_url = match.group(1)
                if not stream_url.startswith('http'):
                    stream_url = urljoin(channel_url, stream_url)
                return stream_url
        
        return None
        
    except Exception as e:
        print_status(f"Stream URL çıkarılırken hata: {e}", "error")
        return None

def generate_m3u_playlist(channels):
    """M3U playlist oluştur"""
    if not channels:
        return None
    
    lines = ["#EXTM3U"]
    valid_channels = 0
    
    for idx, channel in enumerate(channels, 1):
        stream_url = extract_stream_url(channel['url'])
        if stream_url:
            channel_name = f"Golvar2693 - {channel['title']}"
            if channel['type'] == 'live_match':
                channel_name = f"⚽ {channel_name}"
            
            lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name}",{channel_name}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
            lines.append(stream_url)
            
            print_status(f"{idx:02d}. {channel_name}", "success")
            valid_channels += 1
        else:
            print_status(f"{idx:02d}. {channel['title']} (Stream bulunamadı)", "warning")
    
    return "\n".join(lines), valid_channels

def main():
    """Ana fonksiyon"""
    print(f"{CYAN}{BOLD}╔══════════════════════════════════════════╗")
    print(f"║           Golvar2693 IPTV Scanner           ║")
    print(f"╚══════════════════════════════════════════╝{RESET}\n")
    
    base_url = "https://golvar2693.sbs/"
    
    # Ana sayfayı al
    print_status("Ana sayfa yükleniyor...")
    html_content = get_site_content(base_url)
    if not html_content:
        sys.exit(1)
    
    # Kanalları çıkar
    print_status("Kanallar taranıyor...")
    channels = extract_channels_from_html(html_content, base_url)
    
    if not channels:
        print_status("Hiç kanal bulunamadı!", "error")
        
        # Alternatif: Doğrudan bilinen kanal URL'lerini dene
        alternative_channels = [
            {'url': base_url + 'channel.html', 'title': 'Ana Kanal', 'type': 'tv_channel'},
            {'url': base_url + 'live.html', 'title': 'Canlı Yayın', 'type': 'live_match'},
            {'url': base_url + 'tv.html', 'title': 'TV Kanalları', 'type': 'tv_channel'},
        ]
        
        channels = alternative_channels
        print_status("Alternatif kanallar deneniyor...", "warning")
    
    print_status(f"{len(channels)} kanal bulundu", "success")
    
    # M3U playlist oluştur
    print_status("Stream URL'leri çıkarılıyor...")
    playlist, valid_count = generate_m3u_playlist(channels)
    
    if not playlist or valid_count == 0:
        print_status("Hiçbir kanal için stream bulunamadı!", "error")
        sys.exit(1)
    
    # Dosyaya yaz
    filename = "golvar2693.m3u"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(playlist)
        print_status(f"Playlist oluşturuldu: {filename}", "success")
        print_status(f"Aktif kanal sayısı: {valid_count}", "success")
        
    except Exception as e:
        print_status(f"Dosya yazılırken hata: {e}", "error")
        sys.exit(1)
    
    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════════╗")
    print(f"║            İŞLEM TAMAMLANDI              ║")
    print(f"║   Aktif Kanal: {valid_count:2d}                         ║")
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
