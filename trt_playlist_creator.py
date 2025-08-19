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

# TRT ve diğer popüler Türk kanalları
KANALLAR = [
    {"slug": "trt-1", "tvg_id": "TRT1.tr", "kanal_adi": "TRT 1 HD"},
    {"slug": "show-tv", "tvg_id": "ShowTV.tr", "kanal_adi": "Show TV HD"},
    {"slug": "star-tv", "tvg_id": "StarTV.tr", "kanal_adi": "Star TV HD"},
    {"slug": "trt-haber", "tvg_id": "TRTHaber.tr", "kanal_adi": "TRT Haber HD"},
    {"slug": "atv", "tvg_id": "ATV.tr", "kanal_adi": "ATV HD"},
    {"slug": "fox-tv", "tvg_id": "FOX.tr", "kanal_adi": "FOX HD"},
    {"slug": "kanal-d", "tvg_id": "KanalD.tr", "kanal_adi": "Kanal D HD"},
    {"slug": "tv8", "tvg_id": "TV8.tr", "kanal_adi": "TV8 HD"},
    {"slug": "trt-spor", "tvg_id": "TRTSpor.tr", "kanal_adi": "TRT Spor HD"},
    {"slug": "bein-sports", "tvg_id": "BeinSports1.tr", "kanal_adi": "beIN Sports HD"},
    {"slug": "kanal-7", "tvg_id": "Kanal7.tr", "kanal_adi": "Kanal 7 HD"},
    {"slug": "tv100", "tvg_id": "TV100.tr", "kanal_adi": "TV100 HD"},
    {"slug": "a-haber", "tvg_id": "AHaber.tr", "kanal_adi": "A Haber HD"},
    {"slug": "a-news", "tvg_id": "ANews.tr", "kanal_adi": "A News HD"},
    {"slug": "cnnturk", "tvg_id": "CNNTurk.tr", "kanal_adi": "CNN Türk HD"},
    {"slug": "ntv", "tvg_id": "NTV.tr", "kanal_adi": "NTV HD"},
    {"slug": "haberturk", "tvg_id": "Haberturk.tr", "kanal_adi": "Habertürk HD"},
    {"slug": "tlc", "tvg_id": "TLC.tr", "kanal_adi": "TLC HD"},
    {"slug": "tv-8-5", "tvg_id": "TV85.tr", "kanal_adi": "TV8.5 HD"},
    {"slug": "bloomberght", "tvg_id": "BloombergHT.tr", "kanal_adi": "Bloomberg HT HD"},
]

def get_base_url():
    """Temel URL'yi canlitv.top sitesinden al"""
    base_url = "https://www.canlitv.top"
    print(f"{GREEN}[*] CanliTV.top sitesine bağlanılıyor...{RESET}")
    return base_url

def find_stream_url(channel_slug, base_url):
    """Kanalın yayın URL'sini bul"""
    try:
        channel_url = f"{base_url}/{channel_slug}"
        print(f"{BLUE}[*] {channel_slug} kanalı aranıyor...{RESET}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': base_url
        }
        
        response = requests.get(channel_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 1. Iframe içinde arama
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', response.text)
        if iframe_match:
            iframe_src = iframe_match.group(1)
            print(f"{GREEN}[+] Iframe bulundu: {iframe_src}{RESET}")
            return iframe_src
        
        # 2. JavaScript player.setup içinde arama
        player_match = re.search(r'player\.setup\({\s*file\s*:\s*["\']([^"\']+)["\']', response.text)
        if player_match:
            stream_url = player_match.group(1)
            print(f"{GREEN}[+] Player URL bulundu: {stream_url}{RESET}")
            return stream_url
        
        # 3. Source tag'inde arama
        source_match = re.search(r'<source[^>]+src=["\']([^"\']+)["\']', response.text)
        if source_match:
            source_url = source_match.group(1)
            print(f"{GREEN}[+] Source URL bulundu: {source_url}{RESET}")
            return source_url
        
        # 4. M3U8 uzantılı URL'leri ara
        m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', response.text)
        if m3u8_match:
            m3u8_url = m3u8_match.group(1)
            print(f"{GREEN}[+] M3U8 URL bulundu: {m3u8_url}{RESET}")
            return m3u8_url
        
        print(f"{YELLOW}[-] {channel_slug} için stream URL bulunamadı{RESET}")
        return None
        
    except Exception as e:
        print(f"{RED}[!] {channel_slug} hatası: {str(e)}{RESET}")
        return None

def generate_m3u():
    """M3U playlist oluştur"""
    base_url = get_base_url()
    lines = ["#EXTM3U"]
    success_count = 0
    
    for idx, kanal in enumerate(KANALLAR, start=1):
        print(f"\n{BLUE}[{idx}/{len(KANALLAR)}] {kanal['kanal_adi']} işleniyor...{RESET}")
        
        stream_url = find_stream_url(kanal["slug"], base_url)
        
        if stream_url:
            # URL'yi normalize et
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url
            elif stream_url.startswith('/'):
                stream_url = base_url + stream_url
            
            # M3U formatına ekle
            lines.append(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{kanal["kanal_adi"]}",{kanal["kanal_adi"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            lines.append(f'#EXTVLCOPT:http-referrer={base_url}')
            lines.append(stream_url)
            
            print(f"{GREEN}[+] {kanal['kanal_adi']} eklendi{RESET}")
            success_count += 1
        else:
            print(f"{RED}[-] {kanal['kanal_adi']} eklenemedi{RESET}")
        
        # Sunucuya aşırı yük bindirmemek için bekle
        time.sleep(0.5)
    
    return "\n".join(lines), success_count

if __name__ == "__main__":
    print(f"{GREEN}TRT ve Türk Kanalları M3U Playlist Oluşturucu{RESET}")
    print(f"{GREEN}==============================================={RESET}")
    
    playlist, success_count = generate_m3u()
    
    with open("trt_playlist.m3u", "w", encoding="utf-8") as f:
        f.write(playlist)
    
    print(f"\n{GREEN}[+] İşlem tamamlandı!{RESET}")
    print(f"{GREEN}[+] Başarılı kanal sayısı: {success_count}/{len(KANALLAR)}{RESET}")
    print(f"{GREEN}[+] Playlist dosyası: trt_playlist.m3u{RESET}")
    
    if success_count == 0:
        print(f"{RED}[!] Hiçbir kanal bulunamadı. Web sitesi yapısı değişmiş olabilir.{RESET}")
        sys.exit(1)
