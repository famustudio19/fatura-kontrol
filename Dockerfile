FROM python:3.11-slim

# LibreOffice kur (PDF dönüştürme için)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice \
        libreoffice-calc \
        fonts-dejavu \
        fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bağımlılıkları kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Çalışma klasörlerini oluştur
RUN mkdir -p uploads outputs

# Render.com varsayılan portu: 10000
EXPOSE 10000

CMD ["gunicorn", "app:app", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:10000"]
