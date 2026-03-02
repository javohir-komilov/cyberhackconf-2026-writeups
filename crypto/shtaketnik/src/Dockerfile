FROM python:3.11-slim

RUN useradd -m -s /bin/sh ctf

WORKDIR /app

COPY "crypto easy.py" ./server.py

EXPOSE 31337

USER ctf

# FLAG env var injected by whale; server.py reads os.environ["FLAG"]
CMD ["sh", "-c", \
     "FLAG=CHC{rail_fence_cipher_${FLAG}} exec python3 server.py"]
