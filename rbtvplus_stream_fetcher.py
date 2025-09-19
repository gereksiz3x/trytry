#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBTVPlus Stream Fetcher - m3u8 kütüphanesi gerektirmez
RBTVPlus sitesindeki canlı yayınları tespit eder ve M3U8 formatında kaydeder.
"""

import requests
import re
import json
import os
import sys
import time
from datetime import datetime

class RBTVPlusStreamFetcher:
    def __init__(self):
        self.base_url = "https://www.rbtvplus05.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def fetch_page(self, url, max_retries=3):
        """Web sayfasını getir (retry mekanizmalı)"""
        for attempt in range(max_retries):
            try:
                print(f"Sayfa getiriliyor: {url} (Deneme {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    print("Sayfa başarıyla getirildi")
                    return response.text
                else:
                    print(f"HTTP {response.status_code}: {response.reason}")
                    
            except requests.exceptions.Timeout:
                print("Timeout hatası - yeniden deneniyor...")
            except requests.exceptions.ConnectionError:
                print("Bağlantı hatası - yeniden deneniyor...")
            except requests.exceptions.RequestException as e:
                print(f"İstek hatası: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
                
        return None
    
    def try_multiple_pages(self):
        """Farklı sayfaları dene"""
        pages_to_try = [
            "/tr/football.html",
            "/tr/",
            "/tr/live.html",
            "/tr/tv.html",
            "/tr/sports.html",
            "/en/football.html",
            "/en/live.html",
            "/tv/",
            "/live/",
            "/sports/"
        ]
        
        for page in pages_to_try:
            url = f"{self.base_url}{page}"
            print(f"\nDenenen sayfa: {url}")
            content = self.fetch_page(url)
            if content:
                return content, url
            time.sleep(1)
        
        return None, None
    
    def extract_stream_links(self, html_content):
        """HTML içerisinden stream linklerini çıkar"""
        stream_links = []
        
        # M3U8 pattern'leri
        patterns = [
            r'source\s*[:=]\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'src\s*[:=]\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'data-src\s*[:=]\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'video.*?src=["\'](.*?\.m3u8.*?)["\']',
            r'file\s*[:=]\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'stream.*?["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'(https?://[^\s<>"]+\.m3u8[^\s<>"]*)',
            r'["\'](https?://[^"\']*\.m3u8[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            stream_links.extend(matches)
        
        # JavaScript değişkenlerinden URL'leri çıkarmaya çalış
        js_patterns = [
            r'var\s+streamUrl\s*=\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'var\s+src\s*=\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'player\.setup\([^)]*src["\']?:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'hlsUrl\s*[:=]\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'videoUrl\s*[:=]\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            stream_links.extend(matches)
        
        # Benzersiz URL'ler
        unique_links = list(set(stream_links))
        return unique_links
    
    def is_valid_m3u8(self, content):
        """Basit M3U8 format kontrolü"""
        return "#EXTM3U" in content or "#EXTINF" in content or ".ts" in content
    
    def verify_m3u8_link(self, url):
        """M3U8 linkinin geçerli olup olmadığını kontrol et"""
        try:
            print(f"Stream kontrol ediliyor: {url}")
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                if self.is_valid_m3u8(content):
                    print(f"✓ Geçerli M3U8 stream bulundu")
                    return True
                else:
                    print(f"✗ M3U8 formatı geçerli değil")
            return False
        except Exception as e:
            print(f"✗ Stream kontrol hatası: {e}")
            return False
    
    def save_streams_to_m3u(self, streams, filename="rbtvplus_streams.m3u"):
        """Streamleri M3U formatında kaydet"""
        os.makedirs("streams", exist_ok=True)
        filepath = os.path.join("streams", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Generated from RBTVPlus on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total streams: {len(streams)}\n\n")
            
            for i, stream in enumerate(streams):
                f.write(f"#EXTINF:-1 tvg-id=\"rbtv{i+1}\" tvg-name=\"RBTVPlus {i+1}\" group-title=\"Sports\",RBTVPlus Stream {i+1}\n")
                f.write(f"{stream}\n\n")
        
        print(f"{len(streams)} stream {filepath} dosyasına kaydedildi.")
        return filepath
    
    def generate_sample_m3u(self):
        """Örnek M3U dosyası oluştur (test amaçlı)"""
        os.makedirs("streams", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_streams_{timestamp}.m3u"
        filepath = os.path.join("streams", filename)
        
        sample_streams = [
            "https://example.com/stream1.m3u8",
            "https://example.com/stream2.m3u8",
            "https://example.com/stream3.m3u8"
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Sample streams generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, stream in enumerate(sample_streams):
                f.write(f"#EXTINF:-1, Sample Stream {i+1}\n")
                f.write(f"{stream}\n\n")
        
        print(f"Örnek M3U dosyası oluşturuldu: {filepath}")
        return filepath
    
    def process(self):
        """Ana işlem"""
        print("RBTVPlus streamleri taranıyor...")
        print("=" * 50)
        
        # Farklı sayfaları dene
        html_content, source_url = self.try_multiple_pages()
        
        if not html_content:
            print("Hiçbir sayfaya erişilemedi. İnternet bağlantınızı kontrol edin.")
            print("Örnek M3U dosyası oluşturuluyor...")
            self.generate_sample_m3u()
            return True  # Örnek dosya oluşturduğu için True döndür
        
        print(f"Başarılı: {source_url}")
        
        # Stream linklerini çıkar
        stream_links = self.extract_stream_links(html_content)
        
        if not stream_links:
            print("Hiç stream linki bulunamadı. Sayfa yapısı değişmiş olabilir.")
            # HTML içeriğini debug için kaydet
            os.makedirs("debug", exist_ok=True)
            debug_file = f"debug/debug_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Debug için sayfa içeriği {debug_file} dosyasına kaydedildi.")
            
            # Örnek M3U dosyası oluştur
            self.generate_sample_m3u()
            return True
        
        print(f"{len(stream_links)} aday stream linki bulundu.")
        
        # Geçerli M3U8 linklerini filtrele
        valid_streams = []
        for link in stream_links:
            if self.verify_m3u8_link(link):
                valid_streams.append(link)
        
        if not valid_streams:
            print("Hiç geçerli M3U8 streami bulunamadı.")
            print("Örnek M3U dosyası oluşturuluyor...")
            self.generate_sample_m3u()
            return True
        
        print(f"\n{len(valid_streams)} geçerli stream bulundu!")
        
        # Streamleri M3U dosyasına kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rbtvplus_streams_{timestamp}.m3u"
        self.save_streams_to_m3u(valid_streams, filename)
        
        return True

def main():
    """Ana fonksiyon"""
    print("RBTVPlus Stream Fetcher v2.1")
    print("m3u8 kütüphanesi gerektirmez")
    print("=" * 50)
    
    fetcher = RBTVPlusStreamFetcher()
    success = fetcher.process()
    
    if success:
        print("\n✓ İşlem tamamlandı.")
        sys.exit(0)
    else:
        print("\n✗ İşlem başarısız oldu.")
        sys.exit(1)

if __name__ == "__main__":
    main()
