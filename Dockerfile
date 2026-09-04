FROM python:3.11-slim

# FFmpeg e necessario para o streaming de audio.
# curl/unzip para instalar o Deno (runtime JS usado pelo yt-dlp para resolver
# o "n challenge"/assinatura do YouTube; sem ele os formatos ficam indisponiveis).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instala o Deno (runtime JS) em /usr/local/bin para o yt-dlp encontrar no PATH.
ENV DENO_INSTALL=/usr/local
RUN curl -fsSL https://deno.land/install.sh | sh \
    && deno --version

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
