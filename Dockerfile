FROM python:3.11-slim

# FFmpeg e necessario para o streaming de audio.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY melodybot ./melodybot

# Volume para persistir o SQLite.
VOLUME ["/app/data"]

CMD ["python", "-m", "melodybot"]
