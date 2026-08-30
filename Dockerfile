FROM python:3.11-slim

# FFmpeg e necessario para o streaming de audio.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt requirements-full.txt ./
# Instala base + features opcionais (IA e pagamento). Se nao usar, as libs
# ficam ociosas; os providers so ativam quando ha chave no .env.
RUN pip install --no-cache-dir -r requirements-full.txt

COPY melodybot ./melodybot

# Volume para persistir o SQLite.
VOLUME ["/app/data"]

CMD ["python", "-m", "melodybot"]
