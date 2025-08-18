import requests
from bs4 import BeautifulSoup
import re
import os

def extract_stream_url():
    url = "https://www.diycraftsguide.com/live-tv/solh-tv.html"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for iframe or script tags containing the stream
        iframe = soup.find('iframe')
        if iframe and 'src' in iframe.attrs:
            return iframe['src']
            
        # Alternative pattern if iframe doesn't work
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                match = re.search(r'(https?://[^\s]+\.m3u8?)', script.string)
                if match:
                    return match.group(1)
                    
        # If no iframe or script found, try to find video tag
        video = soup.find('video')
        if video and 'src' in video.attrs:
            return video['src']
            
    except Exception as e:
        print(f"Error extracting stream URL: {e}")
    
    return None

def generate_m3u(stream_url):
    if not stream_url:
        return None
        
    m3u_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000
{stream_url}
"""
    return m3u_content

def main():
    stream_url = extract_stream_url()
    if stream_url:
        print(f"Found stream URL: {stream_url}")
        m3u_content = generate_m3u(stream_url)
        
        with open('solh-tv.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("M3U file generated successfully.")
    else:
        print("Could not extract stream URL.")
        # Exit with error code if no URL found
        exit(1)

if __name__ == "__main__":
    main()
