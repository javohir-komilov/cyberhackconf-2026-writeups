FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app/ /app/
COPY scripts/start-web.sh /usr/local/bin/start-web.sh
COPY scripts/start-worker.sh /usr/local/bin/start-worker.sh

RUN groupadd -r ctf \
    && useradd -r -g ctf web \
    && useradd -r -g ctf worker \
    && mkdir -p /app/data /app/public/exports \
    && chgrp -R ctf /app \
    && chmod -R g+rwX /app/data /app/public/exports \
    && echo 'CHC{1_533_1nj3c710n5_1nj3c710n_3v3rywh3r3}' > /flag \
    && chown worker:ctf /flag \
    && chmod 400 /flag

EXPOSE 5000

CMD ["/usr/local/bin/start-web.sh"]
