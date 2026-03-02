FROM python:3.12-slim

# Root bo'lmagan foydalanuvchi
RUN useradd -m -u 1000 ctfuser

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /app/runtime && \
    chown -R ctfuser:ctfuser /app

USER ctfuser

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
