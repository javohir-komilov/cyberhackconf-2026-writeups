# Corrupted Terminal Emulator

| Field | Value |
|-------|-------|
| Category | Misc |
| Points | ? |

## Description

> Our AI terminal crashed during a critical update. The system is now in
> recovery mode. Can you navigate the broken system and unlock it?
>
> `nc <host> 7000`

## Solution

# Corrupted Terminal Emulator — Full Writeup

## Challenge Overview

A "broken AI terminal" exposes itself over TCP. Players must:
1. Decode the corrupted `ls` output to discover filenames.
2. Use `cat` on the right files, decode binary-encoded content, verify MD5.
3. Extract three key parts and assemble the unlock key.
4. Run `unlock <key>` to receive the flag.

---

## Step 0 — Connect

```
nc <host> 7000
```

You'll see a banner and `terminal>` prompt. Type `help` first.

---

## Step 1 — Decode `ls` Output

Run:
```
terminal> ls
```

You'll see lines like:
```
  MTYyMTQ1MTQxMTQ0MTU1MTQ1MDU2MTY0MTcwMTY0
  ...
```

Each line is: **base64( octal_bytes( real_filename ) )**

### Decoding algorithm

```python
import base64

encoded = "MTYyMTQ1MTQxMTQ0MTU1MTQ1MDU2MTY0MTcwMTY0"
octal_str = base64.b64decode(encoded).decode()     # "162145141144155145056164170164"
groups = [octal_str[i:i+3] for i in range(0, len(octal_str), 3)]
filename = "".join(chr(int(g, 8)) for g in groups) # "readme.txt"
print(filename)
```

### All real filenames
| Encoded (example session) | Decoded |
|---|---|
| MTYyMTQ1MTQxMTQ0MTU1MTQ1MDU2MTY0MTcwMTY0 | readme.txt |
| MTUzMTYxMTYzMDU2MTQzMTQ2MTQ3 | sys.cfg |
| MTUzMTYxMTYzMDU2MTQzMTQ2MTQ3 | kernel.log |
| MTU2MTQ1MTY0MTY3MTYxMTYyMDU2MTY0MTcwMTY0 | network.hex |
| MTYxMTU0MTU1MTYzMTQ1MTQzMTUzMDU2MTY0MTcwMTY0 | unlock_guide.txt |

> **Note:** Order is shuffled each session. Fake files (flag.txt, backup.flag, debug.tmp, shadow.bak) are also present.

---

## Step 2 — Decode `cat` Output

Run:
```
terminal> cat kernel.log
```

The output contains noise lines, then:
```
[B2-BEGIN]
0100101101000101...
...
[B2-END]

[MD5] 0367343c43599c43fcc57da47a649901 [/MD5]
```

### Decoding binary (B2) layer

```python
# 1. Collect all lines between [B2-BEGIN] and [B2-END], join them
bits = "01001011..."   # full binary string

# 2. Split into 8-bit groups → bytes → ASCII
decoded = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8)).decode()
print(decoded)

# 3. Verify with MD5
import hashlib
assert hashlib.md5(decoded.encode()).hexdigest() == "0367343c43599c43fcc57da47a649901"
```

---

## Step 3 — Identify and Avoid Decoys

| File | Contents | Real? |
|---|---|---|
| flag.txt | `CHC{fake_f14g_n0t_r341}` | ❌ Decoy |
| backup.flag | Almost-right key, MD5 won't match | ❌ Decoy |
| debug.tmp | Junk bits, no valid markers | ❌ Decoy |
| shadow.bak | Fake /etc/shadow | ❌ Decoy |
| kernel.log | Contains `PART_A = t3rm1nal` | ✅ Real |
| sys.cfg | Contains `PART_B = c0rrupt` | ✅ Real |
| network.hex | Contains `PART_C = d_fx` | ✅ Real |
| readme.txt | Context / hint | ✅ Real |
| unlock_guide.txt | Key construction guide | ✅ Real |

---

## Step 4 — Assemble the Unlock Key

After decoding all three files:

| Part | Value | Source |
|---|---|---|
| A | `t3rm1nal` | kernel.log → `Recovery token alpha:` |
| B | `c0rrupt` | sys.cfg → `token_beta=` |
| C | `d_fx` | network.hex → `suffix_tag:` |

```python
import hashlib
A = "t3rm1nal"
B = "c0rrupt"
C = "d_fx"
key = hashlib.md5((A + B).encode()).hexdigest()[:8] + C
print(key)  # 32c8acd7d_fx
```

**Final unlock key:** `32c8acd7d_fx`

---

## Step 5 — Unlock and Get Flag

```
terminal> unlock 32c8acd7d_fx
```

Response:
```
*** ACCESS GRANTED ***

Flag: CHC{c0rrupt3d_sh3ll_r3p41r3d}
```

---

## Anti-Unintended / Security Notes

- No real shell access: all commands are whitelisted, no `os.system`/`subprocess`/`eval`/`exec`.
- Virtual filesystem in memory; no real file I/O.
- Input sanitized: regex `[a-zA-Z0-9._:\- ]+`, max 100 chars.
- Session timeout: 120 seconds, max 80 commands.
- Flag stored only as runtime-assembled base64 splits; not in plaintext in source.
- Wrong `unlock` key returns only `Access denied.` — no leaks.
- Fake files intentionally mislead: `flag.txt` has wrong flag, `backup.flag` has a broken key, `debug.tmp` has junk bits.
- MD5 validates *correct decoding* — not brute-forceable; solver must actually decode the binary string.


## Flag

`CHC{c0rrupt3d_sh3ll_r3p41r3d}`
