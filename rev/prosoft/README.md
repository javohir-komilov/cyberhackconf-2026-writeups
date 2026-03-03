# ProSoft v1.0

| Field | Value |
|-------|-------|
| Category | Rev |
| Points | ? |

## Description

> You have the binary of "ProSoft v1.0." It ships in two editions: Free and Paid.
> The paid version includes a secret "vault" with important data.
>
> Your goal: access the paid vault and retrieve the flag.

**Files:** `src/crackme`

## Solution

### Step 1 — Identify the binary

```bash
file crackme
# ELF 64-bit LSB executable, x86-64, dynamically linked, stripped
```

### Step 2 — Find the license check

Disassemble and search for the edition gate:

```bash
objdump -d crackme | less
# search: /0xcd
```

Key instructions:

```asm
401159:  movzbl  0x13e2(%rip), %ebx    # reads byte at 0x4024e2
40116a:  cmp     $0xcd, %bl
40116d:  jne     40124e                 # jump to FREE path if not 0xcd
```

- `0xCC` = FREE TRIAL mode
- `0xCD` = PAID mode

### Step 3 — Calculate file offset

`.rodata` section starts at VA `0x402000`, file offset `0x2000`:

```
file_offset = 0x2000 + (0x4024e2 - 0x402000) = 0x24e2
```

### Step 4 — Patch the binary

```python
data = bytearray(open('crackme', 'rb').read())
print(f'Before: 0x{data[0x24e2]:02x}')  # 0xcc
data[0x24e2] = 0xcd
open('crackme_patched', 'wb').write(data)
```

```bash
chmod +x crackme_patched && ./crackme_patched
```

The binary switches to PAID mode → Secret Vault opens → flag is printed.

## Flag

`CHC{r3v3rs3_m4st3r_p4tch3d_y0u}`
