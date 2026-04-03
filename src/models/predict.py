import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

class TarimPulsePredictor:
    def __init__(self, base_path=""):
        print("\n" + "="*50)
        print("🧠 TARIMPULSE TAHMIN MOTORU YUKLENIYOR")
        print("="*50)
        
        self.model_path = os.path.join(base_path, "models", "tarim_model.pkl")
        self.le_urun_path = os.path.join(base_path, "models", "le_urun.pkl")
        self.le_kat_path = os.path.join(base_path, "models", "le_kat.pkl")
        self.feature_list_path = os.path.join(base_path, "models", "feature_list.pkl")
        self.data_path = os.path.join(base_path, "data", "gold", "final_dataset.csv")

        try:
            self.model = joblib.load(self.model_path)
            self.le_urun = joblib.load(self.le_urun_path)
            self.le_kat = joblib.load(self.le_kat_path)
            self.features = joblib.load(self.feature_list_path)
            print("[+] Model ve yardımcı dosyalar başarıyla yüklendi.")
        except Exception as e:
            print(f"[X] Yükleme Hatası: {e}")
            raise

    def run_daily_analysis(self):
        df = pd.read_csv(self.data_path)
        df['tarih'] = pd.to_datetime(df['tarih'])
        
        latest_date = df['tarih'].max()
        print(f"[*] Analiz ediliyor: {latest_date.date()}")

        current_batch = df[df['tarih'] == latest_date].copy()

        current_batch['urun_id'] = self.le_urun.transform(current_batch['hal_urun_adi'])
        current_batch['kat_id'] = self.le_kat.transform(current_batch['ana_kategori'])
        
        current_batch['ay_sin'] = np.sin(2 * np.pi * current_batch['ay_no']/12)
        current_batch['ay_cos'] = np.cos(2 * np.pi * current_batch['ay_no']/12)
        current_batch['gun_sin'] = np.sin(2 * np.pi * current_batch['haftanin_gunu']/7)
        current_batch['gun_cos'] = np.cos(2 * np.pi * current_batch['haftanin_gunu']/7)

        X = current_batch[self.features]
        preds_log = self.model.predict(X)
        current_batch['tahmin_fiyat'] = np.expm1(preds_log)

        current_batch['degisim_yuzde'] = ((current_batch['tahmin_fiyat'] - current_batch['ortalama_fiyat']) / current_batch['ortalama_fiyat']) * 100
        
        report = current_batch[['hal_urun_adi', 'ortalama_fiyat', 'tahmin_fiyat', 'degisim_yuzde']].copy()
        report.columns = ['Ürün Adı', 'Mevcut (TL)', 'Tahmin (TL)', 'Değişim (%)']
        
        print("\n" + "📊" * 15)
        print(f"📈 FİYATI EN ÇOK ARTACAK ÜRÜNLER (Top 5)")
        print(report.sort_values('Değişim (%)', ascending=False).head(5).to_string(index=False))
        
        print("\n📉 FİYATI EN ÇOK DÜŞECEK ÜRÜNLER (Top 5)")
        print(report.sort_values('Değişim (%)', ascending=True).head(5).to_string(index=False))
        print("📊" * 15 + "\n")
        
        return report

if __name__ == "__main__":
    try:
        predictor = TarimPulsePredictor()
        predictor.run_daily_analysis()
    except Exception as e:
        print(f"[X] Beklenmedik Hata: {e}")