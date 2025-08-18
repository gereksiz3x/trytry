import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def extract_stream_url():
    try:
        url = "https://www.diycraftsguide.com/live-tv/solh-tv.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Debug: Save HTML for inspection
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Check for video sources
        video = soup.find('video')
        if video:
            source = video.find('source')
            if source and 'src' in source.attrs:
                return source['src']
        
        # 2. Check for iframes
        iframe = soup.find('iframe')
        if iframe and 'src' in iframe.attrs:
            return iframe['src']
            
        # 3. Search in scripts
        for script in soup.find_all('script'):
            if script.string:
                matches = re.findall(r'(https?://[^\s]+\.m3u8?)', script.string)
                if matches:
                    return matches[0]
                    
        print("No stream URL found in page")
        return None
        
    except Exception as e:
        print(f"Error extracting stream: {str(e)}")
        return None

def generate_m3u():
    stream_url = extract_stream_url()
    if not stream_url:
        print("Failed to get stream URL")
        return False
        
    print(f"Found stream URL: {stream_url}")
    
    m3u_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000
{stream_url}
"""
    with open('solh-tv.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    return True

if __name__ == "__main__":
    if not generate_m3u():
        exit(1)

# scrape_solh_tv.py sonunda bu kontrolü ekleyin
if __name__ == "__main__":
    if create_m3u():
        print("M3U dosyası başarıyla oluşturuldu")
        with open('solh-tv.m3u', 'r') as f:
            print(f.read())
    else:
        print("M3U oluşturma başarısız")
        exit(1)
