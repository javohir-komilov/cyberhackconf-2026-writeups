FROM python:3.12-slim

# Non-root user
RUN addgroup --gid 1001 ctf && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" ctf

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 7000

# FLAG env var injected by whale
CMD ["sh", "-c", \
     "FLAG=CHC{c0rrupt3d_sh3ll_r3p41r3d_${FLAG}} exec su ctf -s /bin/sh -c 'python -u server.py'"]
