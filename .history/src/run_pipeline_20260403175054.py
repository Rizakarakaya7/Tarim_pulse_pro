import os
import json
import subprocess
import sys
import pandas as pd
from datetime import datetime

# Dosya yollarını Docker içindeki /app dizinine göre sabitleyelim
BASE_DIR = os.getcwd()
STATE_FILE = os.path.join(BASE_DIR, "data", "state.json")
DATA_GOLD_PATH = os.path.join(BASE_DIR, "data", "gold", "final_dataset.csv")

def load_state():
    """Sistem hafızasını (state.json) yükler, yoksa varsayılan değerleri döner."""
    if not os.path.exists(STATE_FILE):
        return {"last_run": "2023-01-01", "model_trained_on": "None", "total_rows": 0}
    
    with open(STATE_FILE, "r") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {"last_run": "2023-01-01", "model_trained_on": "None", "total_rows": 0}

def save_state(state):
    """Sistem hafızasını kaydeder."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def run_step(script_name):
    """Alt scriptleri çalıştırır ve hata kontrolü yapar."""
    print(f"\n--- [CALISIYOR] {script_name} ---")
    # Docker içinde 'src' klasörü altında arama yapar
    script_path = os.path.join(BASE_DIR, "src", script_name)
    
    if not os.path.exists(script_path):
        print(f"[X] Hata: {script_path} bulunamadı!")
        return False

    # env ekleyerek alt scriptlerin ana dizini görmesini sağlıyoruz (Import hatalarını önler)
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR

    process = subprocess.run([sys.executable, script_path], env=env, capture_output=False)
    return process.returncode == 0

def main():
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"[*] TarimPulse Sistemi Başlatıldı.")
    print(f"[*] Son Başarılı Çalışma: {state['last_run']}")

    # --- VERİ TOPLAMA VE İŞLEME ADIMLARI ---
    steps = [
        "ingestion/macro_data.py",
        "ingestion/download_exports.py",
        "ingestion/scraper_antalya.py",
        "processing/extract_exports.py",
        "processing/merge_features.py"
    ]

    for step in steps:
        if not run_step(step):
            print(f"[X] {step} aşamasında kritik hata! Pipeline durduruldu.")
            return

    # --- EĞİTİM KONTROLÜ VE MODEL GÜNCELLEME ---
    if os.path.exists(DATA_GOLD_PATH):
        df = pd.read_csv(DATA_GOLD_PATH)
        current_rows = len(df)
        last_total_rows = int(state.get("total_rows", 0))
        
        if current_rows > last_total_rows:
            print(f"[+] Yeni veri tespit edildi ({last_total_rows} -> {current_rows}). Model eğitiliyor...")
            if run_step("models/train_model.py"):
                state["model_trained_on"] = today
                state["total_rows"] = current_rows
                print(f"[OK] Model başarıyla güncellendi.")
        else:
            print(f"[-] Yeni veri artışı yok. Mevcut model (Satır: {current_rows}) kullanılmaya devam ediliyor.")
    else:
        print("[!] Uyarı: Final veri seti (Gold) bulunamadı. Eğitim atlanıyor.")

    # --- TAHMİN ÜRETME ---
    run_step("models/predict.py")
    
    # Durumu kaydet
    state["last_run"] = today
    save_state(state)
    print(f"\n✅ PIPELINE TAMAMLANDI. Sistem Tarihi: {today}")

 
if __name__ == "__main__":
    main()