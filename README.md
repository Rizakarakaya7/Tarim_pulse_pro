# 🚜 TarımPulse Pro: Akıllı Tarım Fiyat Projeksiyon Platformu

**TarımPulse Pro**, hal borsa verilerini, makroekonomik göstergeleri ve ihracat raporlarını yapay zeka ile harmanlayan, tarım sektörü paydaşları için geliştirilmiş uçtan uca bir **Karar Destek Sistemidir (DSS)**.

## 🎯 Projenin Amacı
Piyasadaki fiyat dalgalanmalarını; döviz kurları, brent petrol fiyatları ve dönemsel ihracat hacimleri ile ilişkilendirerek, gelecek 7 gün için yüksek doğruluklu fiyat tahminleri üretmek ve piyasa risklerini minimize etmektir.

## 📊 Model Başarı Raporu (Nisan 2026)
Model, zaman serisi analizi ve gradyan artırma (**XGBoost**) yöntemiyle eğitilmiş olup, test setinde aşağıdaki yüksek performans metriklerine ulaşmıştır:

| Metrik | Değer | Teknik Karşılığı |
| :--- | :--- | :--- |
| **R2 Skoru** | **%86.98** | Piyasadaki varyansın açıklanma oranı |
| **Yönsel Doğruluk** | **%94.69** | Artış/Azalış yönünü doğru bilme başarısı |
| **MAPE** | **%6.02** | Ortalama yüzdesel sapma marjı |
| **MAE** | **5.50 TL** | Tahmin başına ortalama mutlak hata |

## 🏗️ Teknik Mimari ve Veri Hattı (Pipeline)
Sistem, veriyi kaynağından alıp dashboard'a sunana kadar 4 temel katmanda otonom çalışır:

1.  **Ingestion:** Selenium (Antalya Hal), `yfinance` (Dolar/Petrol) ve `requests` (İhracat PDF) entegrasyonu.
2.  **Processing:** PDF veri ekstraksiyonu ve Feature Engineering (Sin/Cos zaman dönüşümleri).
3.  **Modeling:** XGBoost Regressor ile hiper-parametre optimizasyonlu eğitim.
4.  **Dashboard:** Streamlit tabanlı, interaktif analiz ve projeksiyon paneli.

## 🚀 Kurulum ve Çalıştırma

### 🐳 1. Docker ile Başlatma (Hızlı Kurulum)
Proje tamamen Dockerize edilmiştir. Docker Desktop yüklü ise terminale şu komutu yazın:

```bash
docker-compose up --build

2. Veri Güncelleme ve Otonom Yeniden Eğitim
Projeyi indirdiğiniz tarihten (örneğin 6 ay sonra) itibaren en güncel piyasa verilerini çekmek ve modeli bu yeni verilerle otomatik olarak eğitmek için şu komutu kullanın:

```bash
docker exec -it tarimpulse_app python src/run_pipeline.py