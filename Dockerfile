# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Faster apt + basic deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates fonts-liberation libnss3 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright inside the image
RUN python -m playwright install --with-deps chromium

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]


