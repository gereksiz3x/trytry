import requests
import re
import sys
import time

# Terminal renkleri
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Golvar2693 kanal listesi
KANALLAR = [
    {"dosya": "yayin1.m3u8", "tvg_id": "BeinSports1.tr", "kanal_adi": "Bein Sports 1 HD"},
    {"dosya": "yayin2.m3u8", "tvg_id": "BeinSports2.tr", "kanal_adi": "Bein Sports 2 HD"},
    {"dosya": "yayin3.m3u8", "tvg_id": "BeinSports3.tr", "kanal_adi": "Bein Sports 3 HD"},
    {"dosya": "yayin4.m3u8", "tvg_id": "BeinSports4.tr", "kanal_adi": "Bein Sports 4 HD"},
    {"dosya": "yayin5.m3u8", "tvg_id": "BeinSports5.tr", "kanal_adi": "Bein Sports 5 HD"},
    {"dosya": "yayin6.m3u8", "tvg_id": "BeinMax1.tr", "kanal_adi": "Bein Max 1 HD"},
    {"dosya": "yayin7.m3u8", "tvg_id": "BeinMax2.tr", "kanal_adi": "Bein Max 2 HD"},
    {"dosya": "yayin8.m3u8", "tvg_id": "SSport1.tr", "kanal_adi": "S Sport 1 HD"},
    {"dosya": "yayin9.m3u8", "tvg_id": "SSport2.tr", "kanal_adi": "S Sport 2 HD"},
    {"dosya": "yayin10.m3u8", "tvg_id": "SSportPlus.tr", "kanal_adi": "S Sport Plus HD"},
    {"dosya": "yayin11.m3u8", "tvg_id": "TivibuSpor1.tr", "kanal_adi": "Tivibu Spor 1 HD"},
    {"dosya": "yayin12.m3u8", "tvg_id": "TivibuSpor2.tr", "kanal_adi": "Tivibu Spor 2 HD"},
    {"dosya": "yayin13.m3u8", "tvg_id": "TivibuSpor3.tr", "kanal_adi": "Tivibu Spor 3 HD"},
    {"dosya": "yayin14.m3u8", "tvg_id": "SmartSpor1.tr", "kanal_adi": "Smart Spor 1 HD"},
    {"dosya": "yayin15.m3u8", "tvg_id": "SmartSpor2.tr", "kanal_adi": "Smart Spor 2 HD"},
    {"dosya": "yayin16.m3u8", "tvg_id": "TRTSpor.tr", "kanal_adi": "TRT Spor HD"},
    {"dosya": "yayin17.m3u8", "tvg_id": "TRTSporYildiz.tr", "kanal_adi": "TRT Spor Yıldız HD"},
    {"dosya": "yayin18.m3u8", "tvg_id": "ASpor.tr", "kanal_adi": "A Spor HD"},
    {"dosya": "yayin19.m3u8", "tvg_id": "ATV.tr", "kanal_adi": "ATV HD"},
    {"dosya": "yayin20.m3u8", "tvg_id": "TV8.tr", "kanal_adi": "TV8 HD"},
    {"dosya": "yayin21.m3u8", "tvg_id": "NBATV.tr", "kanal_adi": "NBA TV HD"},
    {"dosya": "yayin22.m3u8", "tvg_id": "ExxenSpor1.tr", "kanal_adi": "Exxen Spor 1 HD"},
    {"dosya": "yayin23.m3u8", "tvg_id": "ExxenSpor2.tr", "kanal_adi": "Exxen Spor 2 HD"},
    {"dosya": "yayin24.m3u8", "tvg_id": "ExxenSpor3.tr", "kanal_adi": "Exxen Spor 3 HD"},
]

def get_base_url():
    """Golvar2693 sitesinden base URL'yi al"""
    print(f"{GREEN}[*] Golvar2693 sitesi analiz ediliyor...{RESET}")
    
    try:
        # Ana sayfayı al
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get('https://golvar2693.sbs/', headers=headers, timeout=10)
        response.raise_for_status()
        
        # JavaScript dosyalarında base URL'yi ara
        js_pattern = r'baseurl\s*[:=]\s*["\']([^"\']+)["\']'
        match = re.search(js_pattern, response.text)
        
        if match:
            base_url = match.group(1)
            print(f"{GREEN}[OK] Base URL bulundu: {base_url}{RESET}")
            return base_url
        else:
            # Alternatif arama: script tag'lerinde
            script_pattern = r'<script[^>]*src=["\']([^"\']*\.js)["\']'
            script_matches = re.findall(script_pattern, response.text)
            
            for script_url in script_matches:
                if not script_url.startswith('http'):
                    script_url = 'https://golvar2693.sbs/' + script_url
                
                try:
                    script_response = requests.get(script_url, headers=headers, timeout=10)
                    script_match = re.search(js_pattern, script_response.text)
                    if script_match:
                        base_url = script_match.group(1)
                        print(f"{GREEN}[OK] Base URL bulundu: {base_url}{RESET}")
                        return base_url
                except:
                    continue
            
            print(f"{YELLOW}[WARN] Base URL bulunamadı, varsayılan URL kullanılıyor...{RESET}")
            return "https://golvar2693.sbs/"
    
    except Exception as e:
        print(f"{RED}[HATA] Site analiz edilemedi: {e}{RESET}")
        return None

def check_channel_availability(base_url, channel_file):
    """Kanalın erişilebilir olup olmadığını kontrol et"""
    try:
        test_url = base_url.rstrip('/') + '/' + channel_file
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://golvar2693.sbs/'
        }
        
        response = requests.head(test_url, headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def generate_m3u(base_url):
    """M3U playlist oluştur"""
    print(f"{BLUE}[*] M3U playlist oluşturuluyor...{RESET}")
    
    lines = ["#EXTM3U"]
    active_channels = 0
    
    for idx, channel in enumerate(KANALLAR, 1):
        channel_name = f"Golvar2693 {channel['kanal_adi']}"
        
        # Kanal erişilebilir mi kontrol et
        if check_channel_availability(base_url, channel['dosya']):
            lines.append(f'#EXTINF:-1 tvg-id="{channel["tvg_id"]}" tvg-name="{channel_name}",{channel_name}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            lines.append(f'#EXTVLCOPT:http-referrer=https://golvar2693.sbs/')
            lines.append(base_url.rstrip('/') + '/' + channel['dosya'])
            print(f"{GREEN}  ✔ {idx:02d}. {channel_name}{RESET}")
            active_channels += 1
        else:
            print(f"{YELLOW}  ✗ {idx:02d}. {channel_name} (Ulaşılamıyor){RESET}")
    
    return "\n".join(lines), active_channels

def main():
    """Ana fonksiyon"""
    print(f"{BLUE}=== Golvar2693 M3U Playlist Oluşturucu ==={RESET}")
    
    # Base URL'yi al
    base_url = get_base_url()
    if not base_url:
        print(f"{RED}[HATA] Base URL alınamadı!{RESET}")
        sys.exit(1)
    
    # M3U oluştur
    playlist, active_count = generate_m3u(base_url)
    
    if active_count == 0:
        print(f"{RED}[HATA] Hiçbir kanala erişilemiyor!{RESET}")
        sys.exit(1)
    
    # Dosyaya yaz
    filename = "golvar2693.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(playlist)
    
    print(f"{GREEN}[OK] {active_count} aktif kanal ile playlist oluşturuldu: {filename}{RESET}")
    
    # Ek bilgiler
    print(f"\n{BLUE}[BİLGİ] Kullanım:{RESET}")
    print(f"  • VLC Player: Doğrudan açabilirsiniz")
    print(f"  • IPTV Player: {filename} dosyasını import edin")
    print(f"  • Güncelleme: Bot her çalıştığında yeni linklerle güncellenir")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}[İPTAL] Kullanıcı tarafından durduruldu.{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{RED}[HATA] Beklenmeyen bir hata oluştu: {e}{RESET}")
        sys.exit(1)
