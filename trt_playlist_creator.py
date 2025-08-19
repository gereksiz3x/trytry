import requests
import re
import sys
import time

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
    {"slug": "a-haber", "tvg_id": "AHaber.tr", "kanal_adi": "A Haber HD"},
]

def get_base_url():
    """Temel URL'yi canlitv.top sitesinden al"""
    return "https://www.canlitv.top"

def extract_m3u8_from_player(player_url):
    """Player sayfasından gerçek m3u8 linkini çıkar"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.canlitv.top/'
        }
        
        response = requests.get(player_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Player sayfasındaki m3u8 linklerini ara
        m3u8_patterns = [
            r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'source\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'["\'](https?://[^"\']+\.m3u8\?[^"\']*)["\']'
        ]
        
        for pattern in m3u8_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                # Geçerli bir m3u8 linki bulduk
                for match in matches:
                    if 'm3u8' in match and not any(x in match for x in ['google', 'youtube', 'doubleclick']):
                        return match
        
        # Eğer m3u8 bulamazsak, iframe içinde ara
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', response.text)
        if iframe_match:
            iframe_src = iframe_match.group(1)
            if iframe_src.startswith('//'):
                iframe_src = 'https:' + iframe_src
            elif iframe_src.startswith('/'):
                iframe_src = 'https://www.canlitv.top' + iframe_src
            
            # Iframe'in içeriğini çek ve tekrar ara
            return extract_m3u8_from_player(iframe_src)
            
        return None
        
    except Exception as e:
        print(f"Player hatası: {player_url} - {str(e)}")
        return None

def find_stream_url(channel_slug, base_url):
    """Kanalın yayın URL'sini bul"""
    try:
        channel_url = f"{base_url}/{channel_slug}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': base_url
        }
        
        response = requests.get(channel_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Önce doğrudan m3u8 linklerini ara
        m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', response.text)
        if m3u8_match:
            m3u8_url = m3u8_match.group(1)
            return m3u8_url
        
        # Player linklerini ara
        player_patterns = [
            r'<iframe[^>]+src=["\']([^"\']+)["\']',
            r'player\.setup\({\s*file\s*:\s*["\']([^"\']+)["\']',
            r'src=["\']([^"\']*player[^"\']*)["\']',
            r'https?://[^"\']*/(?:player|online|tv)[^"\']*'
        ]
        
        for pattern in player_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if match and 'http' in match:
                    player_url = match
                    if player_url.startswith('//'):
                        player_url = 'https:' + player_url
                    elif player_url.startswith('/'):
                        player_url = base_url + player_url
                    
                    # Player sayfasından m3u8 çıkar
                    m3u8_url = extract_m3u8_from_player(player_url)
                    if m3u8_url:
                        return m3u8_url
        
        return None
        
    except Exception as e:
        print(f"Hata: {channel_slug} - {str(e)}")
        return None

def generate_m3u():
    """M3U playlist oluştur"""
    base_url = get_base_url()
    lines = ["#EXTM3U"]
    success_count = 0
    
    for kanal in KANALLAR:
        print(f"İşleniyor: {kanal['kanal_adi']}")
        stream_url = find_stream_url(kanal["slug"], base_url)
        
        if stream_url:
            # URL'yi normalize et
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url
            
            # M3U formatına ekle
            lines.append(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{kanal["kanal_adi"]}",{kanal["kanal_adi"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            lines.append(f'#EXTVLCOPT:http-referrer={base_url}')
            lines.append(stream_url)
            
            print(f"✓ Başarılı: {kanal['kanal_adi']}")
            success_count += 1
        else:
            print(f"✗ Başarısız: {kanal['kanal_adi']}")
        
        # Sunucuya aşırı yük bindirmemek için bekle
        time.sleep(1)
    
    return "\n".join(lines), success_count

if __name__ == "__main__":
    print("TRT Playlist Oluşturucu Başlatılıyor...")
    playlist, success_count = generate_m3u()
    
    with open("trt_playlist.m3u", "w", encoding="utf-8") as f:
        f.write(playlist)
    
    print(f"\nİşlem tamamlandı! Başarılı kanal sayısı: {success_count}/{len(KANALLAR)}")
    
    if success_count == 0:
        sys.exit(1)
