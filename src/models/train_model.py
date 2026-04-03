import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

def train_model_pro():
    print("\n🚀 TARIMPULSE PRO: HIPER-EGITIM BASLATILDI")
    
    # Veri yükleme
    if not os.path.exists("data/gold/final_dataset.csv"):
        print("[X] Hata: Dataset bulunamadı!")
        return
        
    df = pd.read_csv("data/gold/final_dataset.csv")
    df['tarih'] = pd.to_datetime(df['tarih'])
    df = df.sort_values('tarih')

    # Zaman özellikleri (Sin/Cos dönüşümü)
    df['ay_sin'] = np.sin(2 * np.pi * df['ay_no']/12)
    df['ay_cos'] = np.cos(2 * np.pi * df['ay_no']/12)
    df['gun_sin'] = np.sin(2 * np.pi * df['haftanin_gunu']/7)
    df['gun_cos'] = np.cos(2 * np.pi * df['haftanin_gunu']/7)

    # Hedef değişken log dönüşümü (Varyansı dengelemek için)
    df['target_log'] = np.log1p(df['ortalama_fiyat'])

    # Encoder işlemleri
    le_urun = LabelEncoder()
    df['urun_id'] = le_urun.fit_transform(df['hal_urun_adi'])
    le_kat = LabelEncoder()
    df['kat_id'] = le_kat.fit_transform(df['ana_kategori'])

    features = [
        'urun_id', 'kat_id', 'dolar_kuru', 'brent_petrol',
        'yil', 'ay_sin', 'ay_cos', 'gun_sin', 'gun_cos',
        'ihracat_miktar_kg', 'ihracat_deger_usd',
        'fiyat_lag_1', 'fiyat_lag_7', 'fiyat_rolling_7'
    ]
    
    X = df[features]
    y = df['target_log']

    # Zaman bazlı Split (%85 Eğitim, %15 Test)
    split_idx = int(len(df) * 0.85)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # XGBoost Regressor Modeli
    model = xgb.XGBRegressor(
        n_estimators=2000,
        learning_rate=0.02,
        max_depth=6,
        min_child_weight=5,
        subsample=0.7,
        colsample_bytree=0.7,
        reg_alpha=0.5,
        reg_lambda=1.0,
        objective='reg:squarederror',
        random_state=42,
        early_stopping_rounds=100 
    )

    print("[*] Hassas egitim yapiliyor...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100
    )

    # Tahminler ve Metrik Hesaplamaları
    preds_log = model.predict(X_test)
    preds = np.expm1(preds_log) 
    actuals = np.expm1(y_test)

    # 1. Regresyon Metrikleri
    mae = mean_absolute_error(actuals, preds)
    rmse = np.sqrt(mean_squared_error(actuals, preds))
    r2 = r2_score(actuals, preds)

    # 2. MAPE (Yüzdesel Ortalama Hata)
    # Sıfıra bölme hatasını önlemek için küçük bir epsilon ekliyoruz
    mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-5))) * 100

    # 3. Yönsel Doğruluk (Directional Accuracy)
    # Fiyatın bir önceki güne göre değişim yönünü (artış/azalış) bilme oranı
    # Test setindeki ardışık günler üzerinden hesaplanır
    actual_direction = np.sign(actuals.values[1:] - actuals.values[:-1])
    pred_direction = np.sign(preds[1:] - actuals.values[:-1])
    dir_acc = np.mean(actual_direction == pred_direction) * 100

    print("\n" + "🌟"*15)
    print(f"📊 TARIMPULSE ANALİZ RAPORU")
    print(f"[*] MAE (Ortalama Hata): {mae:.2f} TL")
    print(f"[*] RMSE (Kritik Hata): {rmse:.2f} TL")
    print(f"[*] MAPE (Yüzdesel Sapma): %{mape:.2f}")
    print(f"[*] R2 Skoru (Başarı Oranı): %{r2*100:.2f}")
    print(f"[*] Yönsel Doğruluk (Yön Bilme): %{dir_acc:.2f}")
    print("🌟"*15)

    # Modelleri kaydet
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/tarim_model.pkl")
    joblib.dump(le_urun, "models/le_urun.pkl")
    joblib.dump(le_kat, "models/le_kat.pkl")
    joblib.dump(features, "models/feature_list.pkl")
    
    print("\n[OK] Model ve yardımcı dosyalar güncellendi.")

if __name__ == "__main__":
    train_model_pro()