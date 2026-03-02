FROM python:3.12-alpine
RUN apk add --no-cache socat
WORKDIR /chall
COPY chall.py .
RUN chmod +x chall.py
EXPOSE 4449
CMD ["socat", "TCP-LISTEN:4449,fork,reuseaddr", "EXEC:'python3 /chall/chall.py',pty,stderr,setsid,sigint"]
