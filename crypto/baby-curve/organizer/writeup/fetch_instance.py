#!/usr/bin/env python3
"""Fetch a transcript from a live The Curve instance and save challenge.json."""

import argparse
import json
import socket
from pathlib import Path


def read_until(reader, marker: str) -> str:
    buf = []
    while True:
        ch = reader.read(1)
        if ch == "":
            raise EOFError(f"connection closed before marker {marker!r}")
        buf.append(ch)
        if "".join(buf).endswith(marker):
            return "".join(buf)


def send_line(writer, line: str) -> None:
    writer.write(line + "\n")
    writer.flush()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch transcript from The Curve service")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--count", type=int, default=11)
    p.add_argument("--out", default="../problem/challenge.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sock = socket.create_connection((args.host, args.port), timeout=10)
    r = sock.makefile("r", encoding="utf-8", errors="ignore", newline="\n")
    w = sock.makefile("w", encoding="utf-8", errors="ignore", newline="\n")

    read_until(r, "option> ")
    send_line(w, "1")
    pub_line = r.readline().strip()
    pub = json.loads(pub_line)

    read_until(r, "option> ")
    send_line(w, "3")
    read_until(r, "> ")
    send_line(w, str(args.count))

    batch_line = r.readline().strip()
    batch = json.loads(batch_line)

    out = {
        "challenge": "The Curve-live",
        "description": "Fetched from live instance",
        "public_key": batch["public_key"],
        "signatures": batch["signatures"],
    }

    out_path.write_text(json.dumps(out, indent=2))
    print(f"[+] wrote {out_path}")
    print(f"[+] signatures: {len(out['signatures'])}")

    try:
        read_until(r, "option> ")
        send_line(w, "5")
    except Exception:
        pass

    w.close()
    r.close()
    sock.close()


if __name__ == "__main__":
    main()
