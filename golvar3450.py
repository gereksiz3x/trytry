import requests
import re
from datetime import datetime

def fetch_golvar3450():
    url = "https://golvar3450.sbs/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print("Hata: Sayfa çekilemedi.", e)
        return

    # Örnek: Yayın linklerini bulmak için regex (site yapısına göre ayarlanmalı)
    pattern = r'https?://[^\s"<>]+\.m3u8?[^\s"<>]*'
    streams = re.findall(pattern, response.text)

    if not streams:
        print("Yayın bulunamadı.")
        return

    # M3U playlist başlığı
    m3u_content = "#EXTM3U\n"
    m3u_content += f"#EXT-X-VERSION:3\n"
    m3u_content += f"#PLAYLIST: Golvar3450 IPTV\n"
    m3u_content += f"#EXTENC:UTF-8\n"
    m3u_content += f"#EXT-X-TARGETDURATION:10\n"
    m3u_content += f"#EXT-X-MEDIA-SEQUENCE:1\n"
    m3u_content += f"#EXT-X-PLAYLIST-TYPE:VOD\n"
    m3u_content += f"#EXT-X-INDEPENDENT-SEGMENTS\n"
    m3u_content += f"#EXT-X-PROGRAM-DATE-TIME:{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}\n"

    # Kanal isimlerini çekmek için örnek regex (siteye göre uyarla)
    channel_pattern = r'<div class="channel">(.*?)</div>'
    channels = re.findall(channel_pattern, response.text, re.DOTALL)

    for i, stream_url in enumerate(streams):
        channel_name = f"Golvar3450 Kanal {i+1}"
        if i < len(channels):
            # Temizleme ve düzenleme
            channel_name = re.sub(r'<[^>]+>', '', channels[i]).strip()[:50]
        
        m3u_content += f'#EXTINF:-1 tvg-id="golvar{i+1}" tvg-name="{channel_name}" group-title="Golvar3450",{channel_name}\n'
        m3u_content += stream_url + "\n"

    # Dosyaya yaz
    with open("golvar3450.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("golvar3450.m3u oluşturuldu.")

if __name__ == "__main__":
    fetch_golvar3450()
