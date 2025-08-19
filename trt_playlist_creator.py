import requests
import re
import sys
import time

# TRT ve diğer popüler Türk kanalları - doğrudan embed linkleri
KANALLAR = [
    {"embed": "https://www.canlitv.top/embed/trt-1", "tvg_id": "TRT1.tr", "kanal_adi": "TRT 1 HD"},
    {"embed": "https://www.canlitv.top/embed/show-tv", "tvg_id": "ShowTV.tr", "kanal_adi": "Show TV HD"},
    {"embed": "https://www.canlitv.top/embed/star-tv", "tvg_id": "StarTV.tr", "kanal_adi": "Star TV HD"},
    {"embed": "https://www.canlitv.top/embed/trt-haber", "tvg_id": "TRTHaber.tr", "kanal_adi": "TRT Haber HD"},
    {"embed": "https://www.canlitv.top/embed/atv", "tvg_id": "ATV.tr", "kanal_adi": "ATV HD"},
    {"embed": "https://www.canlitv.top/embed/fox-tv", "tvg_id": "FOX.tr", "kanal_adi": "FOX HD"},
    {"embed": "https://www.canlitv.top/embed/kanal-d", "tvg_id": "KanalD.tr", "kanal_adi": "Kanal D HD"},
    {"embed": "https://www.canlitv.top/embed/tv8", "tvg_id": "TV8.tr", "kanal_adi": "TV8 HD"},
    {"embed": "https://www.canlitv.top/embed/trt-spor", "tvg_id": "TRTSpor.tr", "kanal_adi": "TRT Spor HD"},
    {"embed": "https://www.canlitv.top/embed/bein-sports", "tvg_id": "BeinSports1.tr", "kanal_adi": "beIN Sports HD"},
    {"embed": "https://www.canlitv.top/embed/kanal-7", "tvg_id": "Kanal7.tr", "kanal_adi": "Kanal 7 HD"},
    {"embed": "https://www.canlitv.top/embed/a-haber", "tvg_id": "AHaber.tr", "kanal_adi": "A Haber HD"},
]

def extract_stream_url(embed_url):
    """Embed sayfasından stream URL'sini çıkar"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(embed_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Debug için response içeriğini kaydet
        with open('debug_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Çeşitli patternlerle stream URL'sini ara
        patterns = [
            r'source\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'file\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'player\.setup\([^)]+file["\']?:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'["\'](https?://[^"\']+\.m3u8\?[^"\']*)["\']',
            r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if 'm3u8' in match and not any(x in match for x in ['google', 'youtube', 'doubleclick', 'ad.']):
                    return match
        
        return None
        
    except Exception as e:
        print(f"Hata ({embed_url}): {str(e)}")
        return None

def generate_m3u():
    """M3U playlist oluştur"""
    lines = ["#EXTM3U"]
    success_count = 0
    
    for kanal in KANALLAR:
        print(f"İşleniyor: {kanal['kanal_adi']}")
        stream_url = extract_stream_url(kanal["embed"])
        
        if stream_url:
            # URL'yi normalize et
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url
            
            # M3U formatına ekle
            lines.append(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{kanal["kanal_adi"]}",{kanal["kanal_adi"]}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            lines.append(f'#EXTVLCOPT:http-referrer=https://www.canlitv.top')
            lines.append(stream_url)
            
            print(f"✓ Başarılı: {kanal['kanal_adi']} - {stream_url}")
            success_count += 1
        else:
            print(f"✗ Başarısız: {kanal['kanal_adi']}")
        
        # Sunucuya aşırı yük bindirmemek için bekle
        time.sleep(2)
    
    return "\n".join(lines), success_count

if __name__ == "__main__":
    print("TRT Playlist Oluşturucu Başlatılıyor...")
    playlist, success_count = generate_m3u()
    
    with open("trt_playlist.m3u", "w", encoding="utf-8") as f:
        f.write(playlist)
    
    print(f"\nİşlem tamamlandı! Başarılı kanal sayısı: {success_count}/{len(KANALLAR)}")
    
    # Debug dosyasını temizle
    try:
        import os
        if os.path.exists('debug_response.html'):
            os.remove('debug_response.html')
    except:
        pass
    
    if success_count == 0:
        sys.exit(1)
