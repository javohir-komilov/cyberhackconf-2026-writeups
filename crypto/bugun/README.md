# Bugun

| Field | Value |
|-------|-------|
| Category | Crypto |
| Points | ? |

## Description

> You are given 3 plaintext-ciphertext pairs and a 4th ciphertext to decrypt.
> Find the pattern and recover the plaintext.

**Files:** `src/crypto.txt`

## Solution

The ciphertext uses an arithmetic progression shift cipher — a variation of Caesar where each character is shifted by a different amount following an arithmetic sequence.

**Pattern analysis from the 3 examples:**

| # | Ciphertext | Plaintext | Step progression |
|---|------------|-----------|-----------------|
| 1 | `uzag_bvquh_ejkq_72lj` | `turt_karra_turt_19ga` | +1, +5, +9, +13, ... (step +4) |
| 2 | `vgo_unhkw_tem_45ro_kykg` | `uch_karra_uch_11ga_teng` | +1, +4, +7, +10, ... (step +3) |
| 3 | `jnpp_tlegr_bfhh_uhsn_40` | `ikki_karra_ikki_teng_5` | +1, +3, +5, +7, ... (step +2) |

**Key insight:** The step between shift increments decreases by 1 each example (4→3→2), so the 4th ciphertext uses step +1 (i.e., shifts +1, +2, +3, +4, ...).

Numbers shift by their positional value too (e.g., `72` at position 14 shifts by 53 forward → `19`). The plaintext meaning confirms the pattern: `4*4=19` (wrong, CTF flavor text), `3*3=11`, `2*2=5`, so the 4th should give `f3vr4lning_0x1rg1_kun1d4`.

**Target ciphertext:** `g5yv9ru9wq_11j14fv17_bmg21y26`

Decode with +1, +2, +3, +4, +5, ... shifts (alphabet wraps at 26):

```
g → f  (shift 1)
5 → 3  (position 2, numeric shift)
y → v  (shift 3)
v → r  (shift 4)
...
```

## Flag

`CHC{f3vr4lning_0x1rg1_kun1d4}`
