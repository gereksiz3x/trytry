#!/usr/bin/env python3
"""
GitHub Pages için otomatik güncelleme scripti
"""

import os
import json
from datetime import datetime
from ssc_scraper import SSCScraper

def update_github_pages():
    """GitHub Pages için güncelleme yap"""
    scraper = SSCScraper()
    m3u_content, channels = scraper.run()
    
    if m3u_content:
        # M3U dosyasını kaydet
        with open('docs/ssc_sports.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        # Index sayfası oluştur
        create_index_page(channels)
        
        print("GitHub Pages updated successfully!")
        return True
    return False

def create_index_page(channels):
    """HTML index sayfası oluştur"""
    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSC Sports Stream Links</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .channel {{ background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin: 10px 0; }}
        .channel-name {{ font-weight: bold; color: #007bff; }}
        .stream-url {{ word-break: break-all; color: #28a745; }}
        .source-url {{ color: #6c757d; font-size: 0.9em; }}
        .last-update {{ text-align: center; color: #666; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SSC Sports Stream Links</h1>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="channels">
"""

    for channel in channels:
        html_content += f"""
            <div class="channel">
                <div class="channel-name">{channel['name']}</div>
                <div class="stream-url">Stream: {channel['stream_url']}</div>
                <div class="source-url">Source: {channel['source_url']}</div>
            </div>
        """

    html_content += """
        </div>
        
        <div class="last-update">
            <p>Playlist link: <a href="ssc_sports.m3u">ssc_sports.m3u</a></p>
            <p>Automatically updated via GitHub Actions</p>
        </div>
    </div>
</body>
</html>
"""

    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    # docs klasörünü oluştur
    os.makedirs('docs', exist_ok=True)
    
    if update_github_pages():
        print("Update completed successfully!")
    else:
        print("Update failed!")
        exit(1)
