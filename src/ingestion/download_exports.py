import os
import requests
import json
import time
from datetime import datetime

def download_akib_reports():
    download_folder = "data/bronze/ihracat_pdf"
    os.makedirs(download_folder, exist_ok=True)
    
    state_path = "data/state.json"
    start_year = 2023
    
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
                start_year = int(state.get("last_run", "2023-01-01")[:4])
        except:
            pass

    current_year = datetime.now().year
    current_month = datetime.now().month
    yillar = list(range(start_year, current_year + 1))
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    print(f"[*] Tarim_Fiyat_Tahmini Ihracat Veri Takibi Baslatildi. Baslangic Yili: {start_year}")
    pdf_count = 0

    for yil in yillar:
        for index, ay in enumerate(aylar):
            if yil == current_year and index >= current_month:
                continue 
            
            file_name = f"{yil}_{ay.upper()}.pdf"
            file_path = os.path.join(download_folder, file_name)
            
            if os.path.exists(file_path): 
                continue

            templates = [
                "https://www.akib.org.tr/files/documents/2025/Bilgi%20Merkezi/EK%C4%B0M%202025%20YMS%20%C4%B0hracat%20De%C4%9Ferlendirme%20Raporu.pdf" if yil == 2025 and ay == "Ekim" else None,
                f"https://www.akib.org.tr/files/documents/{yil}/Bilgi%20Merkezi/May%C4%B1s%20{yil}%20YMS%20%C4%B0hracat%20De%C4%9Ferlendirme%20Raporu.pdf" if ay == "Mayıs" else None,
                f"https://www.akib.org.tr/files/documents/{ay}%20{yil}%20YMS%20%C4%B0hracat%20De%C4%9Ferlendirme%20Raporu.pdf" if yil == 2026 and ay == "Ocak" else None,
                f"https://www.akib.org.tr/files/documents/{yil}/Bilgi%20Merkezi/{ay.upper().replace('İ', '%C4%B0')}%20{yil}%20YMS%20%C4%B0hracat%20De%C4%9Ferlendirme%20Raporu.pdf",
                f"https://www.akib.org.tr/files/documents/{yil}/Haberler/{ay.upper().replace('İ', '%C4%B0')}%20{yil}%20YMS%20%C4%B0hracat%20De%C4%9Ferlendirme%20Raporu.pdf",
                f"https://www.akib.org.tr/files/documents/{yil}/{ay}%20{yil}%20YMS%20İhracat%20Değerlendirme%20Raporu.pdf",
                f"https://www.akib.org.tr/files/documents/2023/Bilgi%20Merkezi2023/{ay}%20{yil}%20YMS%20İhracat%20Değerlendirme%20Raporu.pdf",
                f"https://www.akib.org.tr/files/documents/{yil+1}/Bilgi%20Merkezi/{ay}%20{yil}%20YMS%20İhracat%20Değerlendirme%20Raporu.pdf" if yil < current_year else None
            ]

            success = False
            for url in templates:
                if not url: continue
                try:
                    final_url = url.replace(" ", "%20")
                    res = requests.get(final_url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(res.content)
                        print(f"[+] Indirildi: {file_name}")
                        pdf_count += 1
                        time.sleep(0.3)
                        success = True
                        break
                except: 
                    continue
            
    print(f"\n[!] Ihracat verileri guncellendi. Toplam {pdf_count} yeni rapor eklendi.")

if __name__ == "__main__":
    download_akib_reports()