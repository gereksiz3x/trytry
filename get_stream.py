import requests
import re
import json
from urllib.parse import unquote

def get_parsatv_stream():
    url = "https://www.parsatv.com/m/"
    
    try:
        # Sayfayı çek
        response = requests.get(url)
        response.raise_for_status()
        
        # JavaScript kodları arasında stream linkini ara
        match = re.search(r"hlsStreamUrl\s*=\s*'([^']+)'", response.text)
        if match:
            stream_url = unquote(match.group(1))
            return stream_url
        
        return None
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None

def generate_m3u(stream_url):
    if not stream_url:
        return None
    
    m3u_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2560000
{stream_url}
"""
    return m3u_content

if __name__ == "__main__":
    stream_url = get_parsatv_stream()
    if stream_url:
        m3u_content = generate_m3u(stream_url)
        with open("parsatv.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print("M3U dosyası oluşturuldu!")
    else:
        print("Yayın linki bulunamadı!")
