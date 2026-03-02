FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg curl \
    && pip install playwright requests \
    && playwright install chromium \
    && playwright install-deps chromium \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY bot.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
