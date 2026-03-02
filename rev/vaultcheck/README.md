# VaultCheck

| Field | Value |
|-------|-------|
| Category | Rev |
| Points | 500 |

## Description

> The vault has a password. The vault has an opinion about debuggers.
>
> `nc <host> 4448`
>
> Attachment: `vaultcheck` (stripped binary)

## Solution

# VaultCheck — Writeup (Hard REV / VM + Anti-Debug)

## Challenge Overview

A stripped 64-bit binary asks for a password.
All strings are XOR-encoded. The actual check is performed by a tiny
stack-based VM interpreting encrypted bytecode stored in the binary.
A `ptrace` anti-debug silently corrupts the decryption key.

**Protections:**
| Protection | Status   |
|------------|----------|
| Canary     | ❌ OFF   |
| PIE        | ❌ OFF   |
| NX         | ✅ ON    |
| RELRO      | Partial  |
| Stripped   | ✅ YES   |
| Anti-debug | ✅ YES   |

---

## Step 1 — Reconnaissance

### Connect to the service

```
$ nc <host> 4448
Password: correctpassword
Access denied.
```

### Check in a debugger

```
$ echo "CHC{v1rtu4l_m4ch1n3_r3v3rs3d}" | gdb -q ./vaultcheck -ex run
...
Access denied.
```

Even with the **correct** password, the binary says denied when traced.
This is the first clue: there is an anti-debug mechanism.

---

## Step 2 — Find the Anti-Debug

Open the binary in Ghidra. Look at the entry function (usually `FUN_004011XX`
after startup stubs). Near the top you'll see a call to `ptrace`:

```c
long lVar1 = ptrace(PTRACE_TRACEME, 0, 0, 0);
// ... later ...
if (lVar1 == -1) {
    for (int i = 0; i < 16; i++)
        key[i] ^= 0xFF;
}
```

`ptrace(PTRACE_TRACEME)` returns `-1` when the process is already being
traced (strace, gdb, ltrace). When triggered, every byte of the VM
decryption key is flipped with `0xFF` → bytecode decodes to garbage →
check always fails silently.

### Bypass

**Option A — patch the branch:**
In Ghidra or a hex editor, find the `JNZ` / `JNE` after the ptrace
return value comparison and change it to a `JMP` (unconditional) that
skips the corruption block. Or NOP out the `JNE`.

**Option B — LD_PRELOAD hook:**
```c
// ptrace_hook.c
long ptrace(enum __ptrace_request r, ...) { return 0; }
// gcc -shared -fPIC -o hook.so ptrace_hook.c
// LD_PRELOAD=./hook.so ./vaultcheck
```

**Option C — gdb override:**
```
(gdb) catch syscall ptrace
(gdb) run
(gdb) set $rax = 0
(gdb) continue
```

---

## Step 3 — Identify the VM

With anti-debug bypassed, decompile `main`. You'll see:

1. A 264-byte encrypted array (`bc_enc`)
2. A 16-byte key array (`key_enc`, stored XOR'd with `0xca`)
3. A decode loop: `bc[i] = bc_enc[i] ^ key[i % 16]`
4. A call to a function `vm_exec(vm, bc, 264)`

Inside `vm_exec` is a `while` loop with a `switch` on a byte read from
`bc`. This is the VM dispatch table. Map out the cases:

| Opcode | Behaviour                         |
|--------|-----------------------------------|
| `0x01` | PUSH next byte onto stack         |
| `0x02` | LOAD input[next byte] onto stack  |
| `0x03` | XOR top two stack values          |
| `0x04` | ADD top two stack values          |
| `0x09` | SUB top two stack values          |
| `0x05` | EQ  (push 1 if equal, else 0)     |
| `0x06` | AND top two stack values          |
| `0x08` | HALT — return top of stack        |

---

## Step 4 — Extract and Decrypt the Bytecode

Dump the arrays from the binary (Ghidra: select array → "Copy Special" →
Byte String, or via Python + `pwntools`):

```python
from pwn import *

elf = ELF('./vaultcheck')

# Locate key_enc (16 bytes) and bc_enc (264 bytes) by their content
# or by following references in the decompiler.
# Addresses will vary — use Ghidra cross-references to find them.

KEY_MASK = 0xca
key_enc = elf.read(KEY_ENC_ADDR, 16)
bc_enc  = elf.read(BC_ENC_ADDR,  264)

key = bytes([b ^ KEY_MASK for b in key_enc])
bc  = bytes([bc_enc[i] ^ key[i % 16] for i in range(264)])
print(bc.hex())
```

---

## Step 5 — Disassemble the Bytecode

Write a simple disassembler:

```python
OP = {0x01:'PUSH', 0x02:'LOAD', 0x03:'XOR', 0x04:'ADD',
      0x09:'SUB',  0x05:'EQ',   0x06:'AND', 0x08:'HALT'}

ip = 0
while ip < len(bc):
    op = bc[ip]; ip += 1
    name = OP.get(op, f'?{op:02x}')
    if op in (0x01, 0x02):          # one-byte argument
        arg = bc[ip]; ip += 1
        print(f"  {name}  0x{arg:02x}")
    else:
        print(f"  {name}")
```

The output starts:
```
  PUSH  0x01          ; initial success bit
  LOAD  0x00          ; input[0] ('C')
  PUSH  0x1f          ; key = (0*17+31)=31
  XOR                 ; input[0] ^ 31
  PUSH  0x54          ; expected = 'C'^31 = 84
  EQ
  AND
  LOAD  0x01          ; input[1] ('H')
  PUSH  0x14          ; key = (1*13+7)=20
  ADD                 ; (input[1]+20)&0xff
  PUSH  0x5c          ; expected = ('H'+20)&0xff = 92
  EQ
  AND
  ...
  HALT
```

---

## Step 6 — Recover the Flag

The bytecode encodes three alternating check patterns:

| i mod 3 | Transform                     | Recover input[i]         |
|---------|-------------------------------|--------------------------|
| 0       | `input[i] ^ k == exp`         | `flag[i] = exp ^ k`      |
| 1       | `(input[i]+k)&0xff == exp`    | `flag[i] = (exp-k)&0xff` |
| 2       | `(input[i]-k)&0xff == exp`    | `flag[i] = (exp+k)&0xff` |

where `k` is the first PUSH argument and `exp` is the second PUSH.

Recovery script:

```python
flag = []
i = 2   # skip initial PUSH 0x01
idx = 0
while bc[i] != 0x08:   # until HALT
    assert bc[i] == 0x02            # LOAD
    assert bc[i+2] == 0x01          # PUSH (key)
    k   = bc[i+3]
    op  = bc[i+4]                   # XOR/ADD/SUB
    exp = bc[i+6]                   # expected

    if op == 0x03:   # XOR
        c = exp ^ k
    elif op == 0x04: # ADD
        c = (exp - k) & 0xFF
    elif op == 0x09: # SUB
        c = (exp + k) & 0xFF

    flag.append(chr(c))
    i += 9              # each check block is 9 bytes
    idx += 1

print(''.join(flag))
```

Output: `CHC{v1rtu4l_m4ch1n3_r3v3rs3d}`

---

## Step 7 — Run

```
$ echo "CHC{v1rtu4l_m4ch1n3_r3v3rs3d}" | ./vaultcheck
Password: Access granted.
```

(Without debugger — anti-debug must be patched or bypassed first.)

---

## Key Concepts Covered

- `ptrace(PTRACE_TRACEME)` anti-debug technique and bypass methods
- Stack-based bytecode VM architecture reversal
- XOR-encoded bytecode with a secondary-obfuscated key
- XOR-encoded strings in `.rodata`
- Systematic bytecode disassembly to recover expected values
- Inverting XOR/ADD/SUB to reconstruct the plaintext input

**Flag:** `CHC{v1rtu4l_m4ch1n3_r3v3rs3d}`

