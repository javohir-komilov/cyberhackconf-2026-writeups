# Silent Transmission

| Field | Value |
|-------|-------|
| Category | Crypto |
| Points | ? |

## Description

> During analysis of WWII-era archives, an unknown radio transmission was
> discovered. The message was encrypted using the Enigma I machine.
> Intelligence analysts believe the plaintext contains the fragment: `ENEMYMOVE`

**Files:** `src/cipher.txt`

## Solution

### Crib (known plaintext): `ENEMYMOVE`

**Ciphertext:**
```
VUZRGYQAJZUGDJMCESYEFGPPBASUVUSYUEZYCVNBGINVXLSWKHBALWXGYHVCPXCRXYJVENSGMJVHVUFUKKQXLPULTRWARKOHBOMCGJBWCHST
```

### Step 1 — Find crib position

Enigma rule: **a letter never encrypts to itself**. Slide `ENEMYMOVE` across the ciphertext and check each position for conflicts.

The correct position is where ciphertext `UEZYCVNBG` aligns with `ENEMYMOVE`:
```
E≠U ✓  N≠E ✓  E≠Z ✓  M≠Y ✓  Y≠C ✓  M≠V ✓  O≠N ✓  V≠B ✓  E≠G ✓
```

This gives the **menu** (pairing map):
```
E→U, N→E, E→Z, M→Y, Y→C, M→V, O→N, V→B, E→G
```

### Step 2 — Build the menu and apply Turing bombe

E appears 3 times and M appears twice — this makes a rich menu for the bombe.

Test hypothesis `E ↔ A` → contradiction found (same letter maps to two plugboard partners) ❌
Test `E ↔ B` → no valid rotor path ❌
Test `E ↔ C` → self-encryption found (M→M) ❌
Test `E ↔ Z` → **no contradictions** ✓ → proceed

### Step 3 — Recover plugboard and settings

Working plugboard: `AN EZ HK IJ LM OW PX QV RY ST`

Recovered Enigma settings:
```
Reflector:      UKW-C
Rotor order:    II III I
Ring settings:  K U I
Start position: J E X
```

### Step 4 — Decrypt

Plug the settings into any Enigma I simulator (CrypTool 2, cryptii.com, dcode.fr):

```
Decrypted:
WEATHER REPORT INDICATES ENEMY MOVEMENT NORTH OF COAST STOP
REINFORCEMENTS REQUIRED IMMEDIATELY STOP MAINTAIN RADIO SILENCE
```

## Flag

`CHC{WEATHER_REPORT_RADIO_SILENCE}`
