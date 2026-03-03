# V3k7or

| Field | Value |
|-------|-------|
| Category | Crypto |
| Points | ? |

## Description

> Decode the message hidden in the file.

**Files:** `src/crypto_medium.txt`

## Solution

The challenge file contains three layers:

**Step 1 — Base85 decode → image**

The end of the file contains a Base85-encoded image. Decode it:

```python
import base64
data = open('crypto_medium.txt', 'rb').read()
# find and decode the base85 section
img = base64.b85decode(b85_section)
open('image.png', 'wb').write(img)
```

The image itself is a red herring (distraction). There is also a fake `CTF{}` flag — ignore it.

**Step 2 — Phone keypad encoding**

The actual encoded message is at the end of the file:

```
1^13  9  16807 0^2 343 125 1^13 25 1^12 216 1^5 36 2401 256 25 25 1^13 6561 1^7 64 1^12 216 1^5 36  0^2 125 16807  1^13 3 256
```

Rewrite as base^exponent form:
```
1^13  3^2  7^5   0^2  7^3 5^3  1^13 5^2 ...
```

This is **phone keypad encoding** (T9-style from 1996–2007 era phones):
- `key^n` = press key `n` times
- `3^2` = press `3` twice → letter at position 2 on key 3 = **`e`**
- `7^5` = press `7` five times → **`s`**
- etc.

Decode each group through the standard phone keypad mapping to get the plaintext, then wrap in `CHC{...}`.

## Flag

`CHC{...}` *(dynamic per instance)*
