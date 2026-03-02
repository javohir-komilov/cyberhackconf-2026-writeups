FROM python:3.11-slim

RUN useradd -m -s /bin/sh ctf

WORKDIR /app

COPY server_uz.py ./

EXPOSE 1337

USER ctf

CMD ["python3", "-u", "server_uz.py"]
