import requests
import re
import os
import time
from urllib.parse import urlparse

def find_working_sporcafe(start=5, end=20):
    print("🧭 sporcafe domainleri taranıyor...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for i in range(start, end + 1):
        url = f"https://www.sporcafe-2fd65c4bc314.xyz/"
        alt_url = f"https://www.sporcafe-2fd65c4bc314.xyz/"
        
        for test_url in [url, alt_url]:
            print(f"🔍 Taranıyor: {test_url}")
            try:
                response = requests.get(test_url, headers=headers, timeout=10)
                if response.status_code == 200 and "uxsyplayer" in response.text:
                    print(f"✅ Aktif domain bulundu: {test_url}")
                    return response.text, test_url
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"⚠️ Hata {test_url}: {e}")
                continue

    print("❌ Aktif domain bulunamadı.")
    return None, None

def find_dynamic_player_domain(page_html):
    patterns = [
        r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.stream)',
        r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.live)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, page_html)
        if match:
            return f"https://{match.group(1)}"
    return None

def extract_base_stream_url(html):
    patterns = [
        r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
        r'baseStreamUrl\s*=\s*[\'"]([^\'"]+)',
        r'streamUrl\s*=\s*[\'"]([^\'"]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None

def build_m3u8_links(stream_domain, referer, channel_ids):
    m3u8_links = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": referer,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    for cid in channel_ids:
        try:
            url = f"{stream_domain}/index.php?id={cid}"
            print(f"🔗 Deneniyor: {cid}")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                base_url = extract_base_stream_url(response.text)
                if base_url:
                    # Base URL'yi temizle ve düzelt
                    base_url = base_url.rstrip('/')
                    full_url = f"{base_url}/{cid}/playlist.m3u8"
                    print(f"✅ {cid} için M3U8 bulundu: {full_url}")
                    m3u8_links.append((cid, full_url))
                else:
                    print(f"❌ baseStreamUrl alınamadı: {cid}")
            else:
                print(f"❌ HTTP {response.status_code}: {cid}")
        except Exception as e:
            print(f"⚠️ Hata ({cid}): {e}")
    
    return m3u8_links

def create_backup(filename="1.m3u"):
    """Dosya yedegi olustur"""
    if os.path.exists(filename):
        backup_name = f"{filename}.backup"
        try:
            with open(filename, 'r', encoding='utf-8') as original:
                with open(backup_name, 'w', encoding='utf-8') as backup:
                    backup.write(original.read())
            print(f"📦 Yedek oluşturuldu: {backup_name}")
        except Exception as e:
            print(f"⚠️ Yedek oluşturma hatası: {e}")

def write_m3u_file(m3u8_links, filename="1.m3u", referer=""):
    if not m3u8_links:
        print("❌ Güncelleme yapılamadı: M3U8 linkleri bulunamadı")
        return False

    # Önce yedek oluştur
    create_backup(filename)
    
    # M3U başlığı
    m3u_content = ['#EXTM3U x-tvg-url="https://raw.githubusercontent.com/freebouquet/epg/main/guide.xml"']
    
    # Kanal bilgileri
    channel_info = {
        "sbeinsports-1": ("beIN Sports 1", "beinsports1.png"),
        "sbeinsports-2": ("beIN Sports 2", "beinsports2.png"),
        "sbeinsports-3": ("beIN Sports 3", "beinsports3.png"),
        "sbeinsports-4": ("beIN Sports 4", "beinsports4.png"),
        "sbeinsports-5": ("beIN Sports 5", "beinsports5.png"),
        "sbeinsportsmax-1": ("beIN Sports Max 1", "beinsportsmax1.png"),
        "sbeinsportsmax-2": ("beIN Sports Max 2", "beinsportsmax2.png"),
        "sssport": ("S Sport", "ssport.png"),
        "sssport2": ("S Sport 2", "ssport2.png"),
        # Diğer kanallar için benzer şekilde ekleyin...
    }

    for cid, m3u8_url in m3u8_links:
        channel_name, logo = channel_info.get(cid, (cid, ""))
        
        m3u_content.extend([
            f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{channel_name}" tvg-logo="{logo}" group-title="SPOR",{channel_name}',
            f'#EXTVLCOPT:http-referrer={referer}',
            m3u8_url,
            ''
        ])

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"✅ M3U dosyası güncellendi: {filename}")
        print(f"📊 Toplam {len(m3u8_links)} kanal eklendi")
        return True
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")
        return False

# Kanal ID'leri
channel_ids = [
    "sbeinsports-1", "sbeinsports-2", "sbeinsports-3", "sbeinsports-4", "sbeinsports-5",
    "sbeinsportsmax-1", "sbeinsportsmax-2", "sssport", "sssport2", "ssmartspor", 
    "ssmartspor2", "stivibuspor-1", "stivibuspor-2", "stivibuspor-3", "stivibuspor-4",
    "sbeinsportshaber", "saspor", "seurosport1", "seurosport2", "sf1", "stabiispor", "sssportplus1"
]

if __name__ == "__main__":
    print("🚀 Spor Cafe M3U Güncelleyici Başlatıldı")
    print("=" * 50)
    
    html, referer_url = find_working_sporcafe()

    if html and referer_url:
        print(f"🌐 Referer: {referer_url}")
        stream_domain = find_dynamic_player_domain(html)
        
        if stream_domain:
            print(f"🔗 Yayın domaini: {stream_domain}")
            m3u8_list = build_m3u8_links(stream_domain, referer_url, channel_ids)
            
            if m3u8_list:
                success = write_m3u_file(m3u8_list, referer=referer_url)
                if success:
                    print("🎉 İşlem başarıyla tamamlandı!")
                else:
                    print("💥 M3U dosyası oluşturulamadı!")
            else:
                print("❌ Hiçbir yayın linki oluşturulamadı.")
        else:
            print("❌ Yayın domaini bulunamadı.")
    else:
        print("⛔ Aktif yayın alınamadı.")
    
    print("=" * 50)
