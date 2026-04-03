import pdfplumber
import pandas as pd
import os
import re
import json

pdf_folder = os.path.join("data", "bronze", "ihracat_pdf")
output_path = os.path.join("data", "silver", "monthly_exports.csv")
os.makedirs("data/silver", exist_ok=True)

categories = {
    "DOMATES": "DOMATES", 
    "BİBER": "BİBER", 
    "PATLICAN": "PATLICAN", 
    "KABAK": "KABAK", 
    "HIYAR": "HIYAR (SALATALIK)", 
    "LİMON": "LİMON", 
    "MANDALİNA": "MANDALİNA", 
    "PORTAKAL": "PORTAKAL", 
    "ELMA": "ELMA", 
    "ÜZÜM": "ÜZÜM TAZE", 
    "NAR": "NAR", 
    "MANDARİN": "MANDALİNA"
}

def clean_val(v):
    return float(v.replace(".", "").replace(",", "."))

def run_extraction():
    print("\n--- [SILVER] IHRACAT PDF ANALIZI BASLADI ---")
    
    if not os.path.exists(pdf_folder):
        print(f"[X] Hata: {pdf_folder} klasörü bulunamadı!")
        return

    files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    if not files:
        print("[!] Klasörde işlenecek PDF dosyası bulunamadı.")
        return

    all_data = []

    for file in files:
        try:
            parts = file.replace(".pdf", "").split("_")
            target_year = parts[0]
            month = parts[1]
            
            with pdfplumber.open(os.path.join(pdf_folder, file)) as pdf:
                for page in pdf.pages[:4]:
                    text = page.extract_text()
                    if not text: continue
                    
                    for line in text.split("\n"):
                        upper_line = line.upper()
                        for key, val in categories.items():
                            if key in upper_line:
                                numbers = re.findall(r'[\d\.\,]{4,}', line)
                                
                                if len(numbers) >= 4:
                                    miktar, deger = numbers[2], numbers[3]
                                elif len(numbers) >= 2:
                                    miktar, deger = numbers[0], numbers[1]
                                else: 
                                    continue

                                all_data.append({
                                    "yil": int(target_year),
                                    "ay": month,
                                    "ihracat_urun_adi": val,
                                    "ihracat_miktar_kg": clean_val(miktar),
                                    "ihracat_deger_usd": clean_val(deger)
                                })
                                break
                                
        except Exception as e:
            print(f"   [!] {file} işlenirken hata oluştu: {e}")

    if all_data:
        df = pd.DataFrame(all_data).drop_duplicates(subset=['yil', 'ay', 'ihracat_urun_adi'])
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[OK] {len(df)} adet ihracat verisi silver katmanına kaydedildi.")
    else:
        print("[!] Hiçbir PDF'den veri ayıklanamadı.")

if __name__ == "__main__":
    run_extraction()