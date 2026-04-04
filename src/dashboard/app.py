import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
from datetime import timedelta, datetime

# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="TarımPulse Pro | Haftalık Projeksiyon",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. KURUMSAL TASARIM, RENK DENGESİ VE ARKA FON
st.markdown("""
    <style>
    /* Ana Arka Fon: Soft Slate */
    .stApp { background-color: #eef2f6; }
    
    /* Sidebar (Sol Menü): Ana fonun bir tık koyusu (Derinlik Efekti) */
    section[data-testid="stSidebar"] { 
        background-color: #dee5ed !important; 
        border-right: 1px solid #ccd4dc; 
    }
    
    /* Sidebar İçindeki Yazılar */
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #1a3a3a !important;
    }

    /* Başlığı Ortalama */
    .main-title {
        text-align: center;
        color: #1a3a3a;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 45px;
        margin-bottom: 5px;
        padding-top: 10px;
    }
    .sub-title {
        text-align: center;
        color: #555;
        font-size: 18px;
        margin-bottom: 30px;
    }

    /* KPI Kartları (Beyaz ve Gölgeli) */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 25px !important;
        border-left: 6px solid #2E7D32;
        box-shadow: 0 10px 20px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-5px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); }
    
    /* Metrik Yazı Tipleri */
    div[data-testid="stMetricValue"] { font-size: 38px !important; font-weight: 800; color: #1e3d59; }
    
    /* Tablo Konteynerları */
    .stDataFrame { 
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border: 1px solid #dee2e6;
    }

    /* Footer Gizleme */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 3. VERİ YÜKLEME SİSTEMİ
MODEL_PATH = "models/tarim_model.pkl"
LE_URUN_PATH = "models/le_urun.pkl"
LE_KAT_PATH = "models/le_kat.pkl"
FEAT_PATH = "models/feature_list.pkl"
GOLD_PATH = "data/gold/final_dataset.csv"

@st.cache_resource
def load_assets():
    if not all(os.path.exists(p) for p in [MODEL_PATH, LE_URUN_PATH, GOLD_PATH]):
        return None, None, None, None, None
    try:
        model = joblib.load(MODEL_PATH)
        le_urun = joblib.load(LE_URUN_PATH)
        le_kat = joblib.load(LE_KAT_PATH)
        features = joblib.load(FEAT_PATH)
        df = pd.read_csv(GOLD_PATH)
        df['tarih'] = pd.to_datetime(df['tarih'])
        return model, le_urun, le_kat, features, df
    except:
        return None, None, None, None, None

model, le_urun, le_kat, features, df = load_assets()

if model is None:
    st.error("❌ Veri tabanı veya Model dosyaları eksik. Lütfen pipeline'ı çalıştırın.")
    st.stop()

# --- TARIH REVIZYONU ---
latest_date_in_data = df['tarih'].max()
# Eğer bugünün verisi henüz CSV'ye tam işlenmemişse bile projeksiyonu BUGÜN üzerinden yapıyoruz:
display_date = datetime.now() 
# -----------------------

# 4. SIDEBAR - ÜRÜN SEÇİMİ
st.sidebar.markdown("### 🔍 Arama Merkezi")
all_products = sorted(df['hal_urun_adi'].unique())
selected_product = st.sidebar.selectbox("Ürün Seçiniz:", all_products)
st.sidebar.divider()
st.sidebar.write(f"📅 **Sistem Tarihi:** {display_date.date()}")
st.sidebar.caption("Haftalık piyasa projeksiyon paneli.")

# 5. HAFTALIK TAHMİN MOTORU
# En güncel satırları alıyoruz
current_batch = df[df['tarih'] == latest_date_in_data].copy()
future_batch = current_batch.copy()

# Projeksiyon Hesaplama (Bugün + 7 Gün)
future_date = display_date + timedelta(days=7)

future_batch['tarih'] = future_date
future_batch['yil'] = future_date.year
future_batch['ay_no'] = future_date.month
future_batch['haftanin_gunu'] = future_date.weekday()
future_batch['ay_sin'] = np.sin(2 * np.pi * future_batch['ay_no']/12)
future_batch['ay_cos'] = np.cos(2 * np.pi * future_batch['ay_no']/12)
future_batch['gun_sin'] = np.sin(2 * np.pi * future_batch['haftanin_gunu']/7)
future_batch['gun_cos'] = np.cos(2 * np.pi * future_batch['haftanin_gunu']/7)
future_batch['urun_id'] = le_urun.transform(future_batch['hal_urun_adi'])
future_batch['kat_id'] = le_kat.transform(future_batch['ana_kategori'])

# Modele Gönder
available_features = [f for f in features if f in future_batch.columns]
preds_log = model.predict(future_batch[available_features])
future_batch['tahmin_fiyat'] = np.expm1(preds_log)
future_batch['degisim'] = ((future_batch['tahmin_fiyat'] - future_batch['ortalama_fiyat']) / future_batch['ortalama_fiyat']) * 100

# 6. ORTALANMIŞ BAŞLIKLAR
st.markdown('<div class="main-title">TarımPulse Pro</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{selected_product} | Haftalık Fiyat Öngörüsü</div>', unsafe_allow_html=True)

# 7. KPI KARTLARI (DENGELİ VE ORTALANMIŞ)
prod_data = future_batch[future_batch['hal_urun_adi'] == selected_product].iloc[0]

st.write("")
_, c1, space, c2, _ = st.columns([0.8, 3, 0.4, 3, 0.8])

with c1:
    st.metric(label="📊 Güncel Borsa Fiyatı", value=f"{prod_data['ortalama_fiyat']:.2f} ₺")

with c2:
    target_str = future_date.strftime('%d.%m.%Y')
    st.metric(
        label=f"🔮 {target_str} Tahmini", 
        value=f"{prod_data['tahmin_fiyat']:.2f} ₺", 
        delta=f"{prod_data['degisim']:.2f}%", 
        delta_color="normal" 
    )

st.write("")
st.divider()

# 8. TREND ANALİZİ
st.subheader("📈 Fiyat Değişim Trendi")
hist_data = df[df['hal_urun_adi'] == selected_product].sort_values('tarih').tail(150)

fig = go.Figure()
fig.add_trace(go.Scatter(x=hist_data['tarih'], y=hist_data['ortalama_fiyat'], 
                         name='Fiyatı', line=dict(color='#2E7D32', width=3)))
hist_data['MA7'] = hist_data['ortalama_fiyat'].rolling(7).mean()
fig.add_trace(go.Scatter(x=hist_data['tarih'], y=hist_data['MA7'], 
                         name='Haftalık Trend', line=dict(color='#FFA000', width=2, dash='dot')))

fig.update_layout(template="plotly_white", hovermode="x unified", height=420,
                  margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.05, x=1))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# 9. PİYASA FIRSATLARI VE RİSKLERİ (GÖLGELİ TABLOLAR)
st.subheader("🔍 Haftalık Piyasa Projeksiyonu")
st.write("")

tab_up, tab_down = st.columns(2)

with tab_up:
    st.markdown("##### 🚀 Artış Beklenen Ürünler")
    st.dataframe(future_batch.sort_values('degisim', ascending=False).head(8)
                  [['hal_urun_adi', 'ortalama_fiyat', 'tahmin_fiyat', 'degisim']], 
                  column_config={
                      "hal_urun_adi": "Ürün", 
                      "ortalama_fiyat": "Bugün", 
                      "tahmin_fiyat": "7 Gün Sonra", 
                      "degisim": st.column_config.NumberColumn("Değişim %", format="%.2f")
                  }, hide_index=True, use_container_width=True)

with tab_down:
    st.markdown("##### 📉 Düşüş Beklenen Ürünler")
    st.dataframe(future_batch.sort_values('degisim', ascending=True).head(8)
                  [['hal_urun_adi', 'ortalama_fiyat', 'tahmin_fiyat', 'degisim']], 
                  column_config={
                      "hal_urun_adi": "Ürün", 
                      "ortalama_fiyat": "Bugün", 
                      "tahmin_fiyat": "7 Gün Sonra", 
                      "degisim": st.column_config.NumberColumn("Değişim %", format="%.2f")
                  }, hide_index=True, use_container_width=True)

st.divider()
st.caption(f"© 2026 TarımPulse Pro | Projeksiyon Tarihi: {future_date.date()}")
st.caption(f"Yatırım Tavsiyesi değildir.")