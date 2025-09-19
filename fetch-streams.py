#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBTVPlus M3U8 Stream Çekici
Bu script RBTVPlus sitesindeki canlı yayınları otomatik olarak tespit eder
ve M3U8 formatında kaydeder.
"""

import requests
import re
import json
import os
import sys
from urllib.parse import urljoin, urlparse
import m3u8
from datetime import datetime

class RBTVPlusStreamRecorder:
    def __init__(self):
        self.base_url = "https://www.rbtvplus05.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def fetch_page(self, url):
        """Web sayfasını getir"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Sayfa getirilemedi: {e}")
            return None
    
    def extract_stream_links(self, html_content):
        """HTML içerisinden stream linklerini çıkar"""
        stream_links = []
        
        # M3U8 pattern'leri
        patterns = [
            r'(https?://[^\s<>"]+\.m3u8[^\s<>"]*)',
            r'source\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'src\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'data-src\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'video.*?src=["\'](.*?\.m3u8.*?)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            stream_links.extend(matches)
        
        # JavaScript değişkenlerinden URL'leri çıkarmaya çalış
        js_patterns = [
            r'var\s+streamUrl\s*=\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'var\s+src\s*=\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'player\.setup\([^)]*src["\']?:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            stream_links.extend(matches)
        
        # Benzersiz URL'ler
        unique_links = list(set(stream_links))
        return unique_links
    
    def verify_m3u8_link(self, url):
        """M3U8 linkinin geçerli olup olmadığını kontrol et"""
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                # M3U8 formatını kontrol et
                if "#EXTM3U" in response.text:
                    return True
            return False
        except:
            return False
    
    def save_streams_to_m3u(self, streams, filename="rbtvplus_streams.m3u"):
        """Streamleri M3U formatında kaydet"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Generated from RBTVPlus on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for i, stream in enumerate(streams):
                f.write(f"#EXTINF:-1, RBTVPlus Stream {i+1}\n")
                f.write(f"{stream}\n")
        
        print(f"{len(streams)} stream {filename} dosyasına kaydedildi.")
        return filename
    
    def process(self):
        """Ana işlem"""
        print("RBTVPlus streamleri taranıyor...")
        
        # Football sayfasını getir
        football_url = f"{self.base_url}/tr/football.html"
        html_content = self.fetch_page(football_url)
        
        if not html_content:
            print("Football sayfası alınamadı.")
            return False
        
        # Stream linklerini çıkar
        stream_links = self.extract_stream_links(html_content)
        
        if not stream_links:
            print("Hiç stream linki bulunamadı.")
            return False
        
        print(f"{len(stream_links)} aday stream linki bulundu.")
        
        # Geçerli M3U8 linklerini filtrele
        valid_streams = []
        for link in stream_links:
            if self.verify_m3u8_link(link):
                valid_streams.append(link)
                print(f"Geçerli stream bulundu: {link}")
        
        if not valid_streams:
            print("Hiç geçerli M3U8 streami bulunamadı.")
            return False
        
        # Streamleri M3U dosyasına kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rbtvplus_streams_{timestamp}.m3u"
        self.save_streams_to_m3u(valid_streams, filename)
        
        return True

def main():
    """Ana fonksiyon"""
    recorder = RBTVPlusStreamRecorder()
    success = recorder.process()
    
    if success:
        print("İşlem başarıyla tamamlandı.")
        sys.exit(0)
    else:
        print("İşlem başarısız oldu.")
        sys.exit(1)

if __name__ == "__main__":
    main()
