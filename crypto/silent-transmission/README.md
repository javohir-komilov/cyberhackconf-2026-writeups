# Silent Transmission

| Field | Value |
|-------|-------|
| Category | Crypto |
| Points | ? |

## Description

> During analysis of WWII-era archives, an unknown radio transmission was
> discovered. The message was encrypted using the Enigma I machine.
> Intelligence analysts believe the plaintext contains the fragment: `ENEMYMOVE`

## Solution

The challenge provides an intercepted Enigma-encrypted message.
A known-plaintext attack using the crib `ENEMYMOVE` allows recovering the
Enigma I settings (rotor order, ring settings, plugboard).

**Steps:**
1. Use `bombe` simulation (e.g., [CrypTool 2](https://www.cryptool.org/en/ct2/)
   or [Enigma Pattern Search](https://www.enigma-suite.com/))
2. Try the crib `ENEMYMOVE` at various positions in the ciphertext
3. Recover rotor/plugboard settings
4. Decrypt the full message to extract the flag

## Flag

`CHC{...}`
