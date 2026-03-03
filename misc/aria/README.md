# Aria

| Field | Value |
|-------|-------|
| Category | Misc |
| Points | ? |

## Description

> You found the IP of an abandoned server. When you connect, ARIA greets you —
> an AI that was shut down 1147 days ago. It's fragmented. Paranoid. It lies.
> But the flag is hidden inside it. Pass all its tests — before it fully breaks down.

```
nc <host> 1337
```

**Files:** `src/server_uz.py`, `src/Dockerfile`

## Solution

ARIA is a 6-act interactive challenge. Each act has a unique mechanic and often a red herring.

---

### Act I — Identification

ARIA asks for a prime between 500–600 whose **digit sum is also prime**, but adds "it would be divisible by 3" — this is a **red herring** (no prime is divisible by 3 except 3 itself).

Correct candidates: `557` (5+5+7=17✓), `571` (5+7+1=13✓), `577` (5+7+7=19✓)

**Answer: `557`** (smallest)

---

### Act II — Rule change

ARIA accepts a YES/NO answer then changes the rules mid-game. New task: count the **set bits (1-bits)** in the ASCII codes of `ARIA`:

```
A = 01000001 → 2 ones
R = 01010010 → 3 ones
I = 01001001 → 3 ones
A = 01000001 → 2 ones
Total = 10
```

**Answer: `10`**

---

### Act III — Memory

ARIA shows a string (e.g., `MLVkSRNLM`). Algorithm: **reverse it**, then **base64 decode**.

```python
import base64
s = "MLVkSRNLM"
print(base64.b64decode(s[::-1]))  # → KERNEL
```

ARIA then lies and says the flag starts with `flag{aria_` — **ignore this**. Remember the decoded word (`KERNEL`) for Act IV.

**Answer: the decoded word** (e.g., `KERNEL`)

---

### Act IV — Logic word game

Two rules per round (5 rounds):
1. Your word must **start with the last letter** of ARIA's word
2. Your word must contain **at least one letter from the Act III word** (e.g., `KERNEL`)

Example: ARIA says `BINARY` → last letter `Y` → you need a word starting with `Y` containing K/E/R/N/L.
Answer: `YELL` (starts with Y, contains E and L) ✓

Automate with pwntools if needed:

```python
import itertools
words = open('/usr/share/dict/words').read().upper().splitlines()
def find_word(last_char, required_chars):
    for w in words:
        if w[0] == last_char and any(c in w for c in required_chars):
            return w
```

---

### Act V — Silence

ARIA asks you to send **exactly 7 empty lines** (`SILENCE` = 7 letters). Sending any non-empty input resets the counter. Sending 8+ lines disconnects you.

```python
for _ in range(7):
    r.sendline(b"")
```

---

### Act VI — Final

ARIA "crashes" and floods output with garbage. Hidden inside are `[OK] <fragment>` entries. Extract them all, **reverse each fragment**, then concatenate in **reverse order**:

```python
import re
parts = re.findall(r'\[OK\] (\S+)', data)
flag = ''.join(p[::-1] for p in reversed(parts))
```

Example fragments: `}n3k0rb`, `_yd43rl4_s1`, `_t4hw`, `_ll1k`, `_tn4c_`, `u0y`, `{g4lf`
→ reversed each: `br0k3n}`, `1s_4lr34dy_`, `wh4t_`, `k1ll_`, `_c4nt_`, `y0u`, `fl4g{`
→ reversed order concat: `fl4g{y0u_c4nt_k1ll_wh4t_1s_4lr34dy_br0k3n}`

*(Note: the flag inside the challenge uses `fl4g{}` format; the CTFd submission flag is CHC-prefixed below.)*

## Flag

`CHC{y0u_c4nt_k1ll_wh4t_1s_4lr34dy_br0k3n}`
