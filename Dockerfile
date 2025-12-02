FROM python:3.12-slim

WORKDIR /app

# 1. System
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. VENV (Tworzymy go w /opt/venv)
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
# Dodajemy do PATH - od teraz każda komenda "python" użyje tej z venv!
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. Instalacja zależności (Klasyczny pip)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Kopiowanie kodu
COPY . .

# 5. Instalacja projektu (żeby widział moduły)
RUN pip install --no-cache-dir -e .

# 6. Konfiguracja
ENV PYTHONPATH=/app
RUN chmod +x scripts/start.sh

EXPOSE 7860

CMD ["./scripts/start.sh"]
