import os
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import StringIO

MAPPING = {
    "Domates": "DOMATES", "Domates (Ceri)": "DOMATES", "Domates (Pembe)": "DOMATES", "Domates Kokteyl": "DOMATES",
    "Biber (Dolma)": "BİBER", "Biber Cin": "BİBER", "Biber Çarli": "BİBER", "Biber Kapya": "BİBER", "Biber Sivri": "BİBER", "Biber Üçburun": "BİBER",
    "Patlıcan": "PATLICAN", "Patlıcan (Topak)": "PATLICAN",
    "Kabak (Bal)": "KABAK", "Kabak (Sakız)": "KABAK",
    "Hıyar": "HIYAR (SALATALIK)", "Hıyar (Slor Paket)": "HIYAR (SALATALIK)",
    "Elma (Golden)": "ELMA", "Elma (Grann Smith)": "ELMA", "Elma (Starking)": "ELMA",
    "Limon": "LİMON", "Lime Limon": "LİMON",
    "Mandarin(Paket)": "MANDALİNA",
    "Portakal (Sıkmalık)": "PORTAKAL", "Portakal (Valencia Pak)": "PORTAKAL"
}

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    if os.path.exists("/usr/bin/google-chrome"):
        chrome_options.binary_location = "/usr/bin/google-chrome"

    try:
        service = Service("/usr/bin/chromedriver") if os.path.exists("/usr/bin/chromedriver") else None
        if service:
            return webdriver.Chrome(service=service, options=chrome_options)
        return webdriver.Chrome(options=chrome_options)
    except:
        from webdriver_manager.chrome import ChromeDriverManager
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def is_warning_present(driver):
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        warnings = ["güncel hal fiyatları yayınlanmadı", "yayınlanmış son hal fiyatları gösterilmektedir"]
        return any(w in body_text for w in warnings)
    except:
        return False

def fetch_data(driver, target_date, save=True):
    formatted_date = target_date.strftime("%d.%m.%Y")
    url = f"https://www.antalya.bel.tr/tr/halden-gunluk-fiyatlar?halyerleri=67b1db61b752f39216d8392d&fiyattarih={formatted_date}"
    
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        if is_warning_present(driver):
            return False, "Güncel veri yok"

        tables = pd.read_html(StringIO(driver.page_source))
        if not tables:
            return False, "Tablo bulunamadı"

        df = max(tables, key=len)
        filtered_rows = []
        
        for _, row in df.iterrows():
            raw_name = str(row.iloc[1]).strip()
            matched_cat = next((cat for key, cat in MAPPING.items() if key.lower() in raw_name.lower()), None)
            
            if matched_cat:
                def clean(v):
                    return str(v).split(' ')[0].replace(".", "").replace(",", ".")

                filtered_rows.append({
                    "tarih": target_date.strftime("%Y-%m-%d"),
                    "hal_urun_adi": raw_name,
                    "ihracat_kategorisi": matched_cat,
                    "birim": row.iloc[-1],
                    "fiyat_min": clean(row.iloc[2]),
                    "fiyat_max": clean(row.iloc[3])
                })

        if filtered_rows:
            res_df = pd.DataFrame(filtered_rows)
            if save:
                path = os.path.join("data", "bronze", f"hal_{target_date.strftime('%Y-%m-%d')}.csv")
                res_df.to_csv(path, index=False, encoding='utf-8-sig')
            return True, res_df
        return False, "Eşleşen ürün yok"
    except Exception as e:
        return "error", str(e)

def fetch_previous_valid_data(driver, date, max_lookback=20):
    for i in range(1, max_lookback + 1):
        prev_date = date - timedelta(days=i)
        success, result = fetch_data(driver, prev_date, save=False)
        if success is True:
            return result
    return None

if __name__ == "__main__":
    bronze_dir = os.path.join("data", "bronze")
    os.makedirs(bronze_dir, exist_ok=True)
    state_path = os.path.join("data", "state.json")
    
    start_date = datetime(2023, 1, 1)
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
                start_date = datetime.strptime(state.get("last_run", "2023-01-01"), "%Y-%m-%d")
        except:
            pass

    driver = init_driver()
    curr, end_date = start_date, datetime.now()
    last_valid_df = None 

    prev_file = os.path.join(bronze_dir, f"hal_{(start_date - timedelta(days=1)).strftime('%Y-%m-%d')}.csv")
    if os.path.exists(prev_file):
        try: last_valid_df = pd.read_csv(prev_file)
        except: pass

    try:
        while curr <= end_date:
            d_str = curr.strftime("%Y-%m-%d")
            file_path = os.path.join(bronze_dir, f"hal_{d_str}.csv")
            
            if os.path.exists(file_path):
                try: last_valid_df = pd.read_csv(file_path)
                except: pass
                curr += timedelta(days=1)
                continue
            
            if curr.weekday() == 6 and last_valid_df is not None:
                df_copy = last_valid_df.copy()
                df_copy["tarih"] = d_str
                df_copy.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                success, result = fetch_data(driver, curr)
                if success is True:
                    last_valid_df = result
                elif success is False and last_valid_df is not None:
                    df_copy = last_valid_df.copy()
                    df_copy["tarih"] = d_str
                    df_copy.to_csv(file_path, index=False, encoding='utf-8-sig')
                elif success is False:
                    fallback = fetch_previous_valid_data(driver, curr)
                    if fallback is not None:
                        fallback["tarih"] = d_str
                        fallback.to_csv(file_path, index=False, encoding='utf-8-sig')
                        last_valid_df = fallback

            time.sleep(1)
            curr += timedelta(days=1)
    finally:
        driver.quit()