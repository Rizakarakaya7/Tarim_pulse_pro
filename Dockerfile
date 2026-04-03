FROM python:3.11-slim

WORKDIR /app

# Sistem paketlerini ve Chrome'u daha güvenli bir yolla kuralım
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgomp1 \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# EĞER SCRAPER KULLANMIYORSAN BURADAN SONRASINI SİLEBİLİRSİN:
# Chrome kurulumu (Modern yöntem)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]