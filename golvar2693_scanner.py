import requests
import sys

# Renkli çıktı için
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_status(message, status="info"):
    if status == "success":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "error":
        print(f"{RED}✗{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}!{RESET} {message}")
    else:
        print(f"* {message}")

def test_stream_urls():
    """Test edilmiş stream URL'lerini dene"""
    print_status("Stream URL'leri test ediliyor...")
    
    stream_urls = [
        # Öncelikli URL'ler
        "https://golvar2693.sbs/stream/live.m3u8",
        "https://golvar2693.sbs/hls/stream.m3u8",
        "https://golvar2693.sbs/live/stream.m3u8",
        "https://golvar2693.sbs/tv/stream.m3u8",
        
        # Alternatif URL'ler
        "https://golvar2693.sbs/stream1.m3u8",
        "https://golvar2693.sbs/channel1.m3u8",
        "https://golvar2693.sbs/live1.m3u8",
    ]
    
    working_urls = []
    
    for url in stream_urls:
        try:
            response = requests.head(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://golvar2693.sbs/'
            })
            
            if response.status_code == 200:
                print_status(f"Çalışıyor: {url}", "success")
                working_urls.append(url)
            else:
                print_status(f"HTTP {response.status_code}: {url}", "warning")
                
        except requests.exceptions.RequestException as e:
            print_status(f"Erişilemiyor: {url} - {e}", "warning")
    
    return working_urls

def create_m3u_playlist(stream_urls):
    """M3U playlist oluştur"""
    if not stream_urls:
        return None
    
    lines = ["#EXTM3U"]
    
    for i, url in enumerate(stream_urls, 1):
        channel_name = f"Golvar2693 Stream {i}"
        lines.append(f'#EXTINF:-1 tvg-id="",{channel_name}')
        lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
        lines.append(url)
    
    return "\n".join(lines)

def main():
    print("Golvar2693 Stream Scanner")
    print("=" * 40)
    
    # Önce siteye erişimi test et
    try:
        response = requests.get("https://golvar2693.sbs/", timeout=10)
        if response.status_code == 200:
            print_status("Siteye erişim başarılı", "success")
        else:
            print_status(f"Site HTTP {response.status_code}", "warning")
    except:
        print_status("Siteye erişilemiyor", "error")
        # Yine de devam et, belki stream URL'leri çalışıyordur
    
    # Stream URL'lerini test et
    working_urls = test_stream_urls()
    
    if not working_urls:
        print_status("Hiçbir stream URL'si çalışmıyor", "error")
        
        # Yedek URL'ler deneyelim
        backup_urls = [
            "https://golvar2693.sbs/stream/",
            "https://golvar2693.sbs/live/",
            "https://golvar2693.sbs/hls/",
        ]
        
        for url in backup_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print_status(f"Yedek URL çalışıyor: {url}", "success")
                    working_urls.append(url)
            except:
                continue
    
    # M3U oluştur
    if working_urls:
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
    else:
        print_status("M3U dosyası oluşturulamadı", "error")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
