import pandas as pd
import numpy as np
import os
import json
from glob import glob

def merge_features_refined():
    print("\n--- [GOLD] VERI BIRLESTIRME VE OZELLIK MUHENDISLIGI BASLADI ---")
    
    bronze_hal_dir = os.path.join("data", "bronze")
    silver_dir = os.path.join("data", "silver")
    gold_dir = os.path.join("data", "gold")
    os.makedirs(gold_dir, exist_ok=True)

    hal_files = glob(os.path.join(bronze_hal_dir, "hal_*.csv"))
    if not hal_files:
        print("[X] Hata: Bronze katmanında hal verisi bulunamadı!")
        return

    df_hal = pd.concat([pd.read_csv(f) for f in hal_files], ignore_index=True)
    df_hal['tarih'] = pd.to_datetime(df_hal['tarih'])
    
    df_hal = df_hal.rename(columns={
        'fiyat_min': 'min', 
        'fiyat_max': 'max',
        'ihracat_kategorisi': 'ana_kategori'
    })

    df_hal['min'] = pd.to_numeric(df_hal['min'], errors='coerce')
    df_hal['max'] = pd.to_numeric(df_hal['max'], errors='coerce')
    df_hal['ortalama_fiyat'] = (df_hal['min'] + df_hal['max']) / 2

    macro_path = os.path.join(silver_dir, "macro_data.csv")
    export_path = os.path.join(silver_dir, "monthly_exports.csv")
    
    if not os.path.exists(macro_path) or not os.path.exists(export_path):
        print("[X] Hata: Silver katmanındaki makro veya ihracat verileri eksik!")
        return

    df_macro = pd.read_csv(macro_path)
    df_exports = pd.read_csv(export_path)
    df_macro['tarih'] = pd.to_datetime(df_macro['tarih'])
    
    month_map = {"OCAK": 1, "ŞUBAT": 2, "MART": 3, "NISAN": 4, "MAYIS": 5, "HAZIRAN": 6,
                 "TEMMUZ": 7, "AĞUSTOS": 8, "EYLÜL": 9, "EKIM": 10, "KASIM": 11, "ARALIK": 12}
    df_exports['ay_no'] = df_exports['ay'].str.upper().map(month_map)

    final_df = pd.merge(df_hal, df_macro, on='tarih', how='outer')
    final_df['yil'] = final_df['tarih'].dt.year
    final_df['ay_no'] = final_df['tarih'].dt.month
    final_df['gun_no'] = final_df['tarih'].dt.day
    final_df['haftanin_gunu'] = final_df['tarih'].dt.dayofweek

    final_df = pd.merge(
        final_df, 
        df_exports, 
        left_on=['yil', 'ay_no', 'ana_kategori'], 
        right_on=['yil', 'ay_no', 'ihracat_urun_adi'],
        how='left'
    )

    print("[*] Ürün bazlı geçmiş veriler ve boşluk doldurma (ffill) işleniyor...")
    final_df = final_df.sort_values(['hal_urun_adi', 'tarih'])

    # KRİTİK DÜZELTME: Ürün bazında gruplayarak boş günleri önceki günle dolduruyoruz
    cols_to_fill = ['ortalama_fiyat', 'ana_kategori', 'dolar_kuru', 'brent_petrol', 
                    'ihracat_miktar_kg', 'ihracat_deger_usd']
    
    for col in cols_to_fill:
        if col in final_df.columns:
            final_df[col] = final_df.groupby('hal_urun_adi', group_keys=False)[col].apply(lambda x: x.ffill())

    # Gecikmeli verileri (Lag) doldurulmuş fiyat üzerinden tekrar hesapla
    for urun in final_df['hal_urun_adi'].unique():
        if pd.isna(urun): continue
        mask = final_df['hal_urun_adi'] == urun
        final_df.loc[mask, 'fiyat_lag_1'] = final_df.loc[mask, 'ortalama_fiyat'].shift(1)
        final_df.loc[mask, 'fiyat_lag_7'] = final_df.loc[mask, 'ortalama_fiyat'].shift(7)
        final_df.loc[mask, 'fiyat_rolling_7'] = final_df.loc[mask, 'ortalama_fiyat'].rolling(window=7).mean()

    # En başta kalan NaN değerleri temizle (Artık gönül rahatlığıyla 0 diyebiliriz)
    final_df = final_df.dropna(subset=['hal_urun_adi']).fillna(0)
    
    drop_cols = ['ihracat_urun_adi', 'ay', 'min', 'max']
    final_df = final_df.drop(columns=[c for c in drop_cols if c in final_df.columns])

    output_path = os.path.join(gold_dir, "final_dataset.csv")
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"[OK] GOLD DATASET TEMIZLENDI VE HAZIRLANDI.")
    print(f"[*] Toplam Satır: {len(final_df)} | Konum: {output_path}")

if __name__ == "__main__":
    merge_features_refined()