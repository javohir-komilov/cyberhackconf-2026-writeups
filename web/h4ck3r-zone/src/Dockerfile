FROM python:3.11-slim

RUN useradd -m -s /bin/sh ctf

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

USER ctf

CMD ["sh", "-c", \
     "echo \"CHC{5QL_1nj3ct10n_4nd_5ST1_m4st3r_hacker_2024_${FLAG}}\" > flag.txt && \
      exec python3 app.py"]
