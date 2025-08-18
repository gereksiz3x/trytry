import requests
import re
import json
from urllib.parse import unquote
from datetime import datetime

def get_parsatv_stream():
    url = "https://www.parsatv.com/m/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Güncel regex pattern
        match = re.search(r"source:\s*'([^']+)'", response.text)
        if not match:
            match = re.search(r"hlsStreamUrl\s*=\s*'([^']+)'", response.text)
        
        if match:
            stream_url = unquote(match.group(1))
            if not stream_url.startswith('http'):
                stream_url = 'https:' + stream_url
            return stream_url
        
        print("Hata: Stream URL bulunamadı. Sayfa yapısı değişmiş olabilir.")
        return None
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        return None

def generate_m3u(stream_url):
    if not stream_url:
        return None
    
    return f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2560000,RESOLUTION=1280x720
{stream_url}
"""

if __name__ == "__main__":
    print(f"Checking Pars TV stream at {datetime.now().isoformat()}")
    stream_url = get_parsatv_stream()
    if stream_url:
        print(f"Stream URL found: {stream_url}")
        m3u_content = generate_m3u(stream_url)
        with open("parsatv.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
    else:
        print("No stream URL found")
