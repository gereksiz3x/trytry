import requests
import re
from datetime import datetime

def fetch_golvar3450():
    url = "https://golvar3450.sbs/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print("Sayfa çekiliyor...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("Sayfa başarıyla çekildi")
    except Exception as e:
        print("Hata: Sayfa çekilemedi.", e)
        return False

    # Hata ayıklama için içeriği kontrol et
    print(f"Sayfa uzunluğu: {len(response.text)} karakter")
    
    # Daha geniş bir regex pattern'i deneyelim
    pattern = r'https?://[^\s"<>]+\.(m3u8|ts|mp4)[^\s"<>]*'
    streams = re.findall(pattern, response.text)
    
    print(f"Bulunan stream sayısı: {len(streams)}")
    
    if not streams:
        print("Yayın bulunamadı. Sayfanın bir kısmını gösteriyorum:")
        print(response.text[:1000])  # İlk 1000 karakteri göster
        return False

    # M3U playlist başlığı
    m3u_content = "#EXTM3U\n"
    
    for i, stream_url in enumerate(streams[:50]):  # İlk 50 stream ile sınırla
        channel_name = f"Golvar3450 Kanal {i+1}"
        
        m3u_content += f'#EXTINF:-1 tvg-id="golvar{i+1}" tvg-name="{channel_name}" group-title="Golvar3450",{channel_name}\n'
        m3u_content += stream_url + "\n"

    # Dosyaya yaz
    try:
        with open("golvar3450.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print("golvar3450.m3u başarıyla oluşturuldu.")
        return True
    except Exception as e:
        print("Dosya yazma hatası:", e)
        return False

if __name__ == "__main__":
    fetch_golvar3450()
