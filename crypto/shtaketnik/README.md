# Shtaketnik

| Field | Value |
|-------|-------|
| Category | Crypto |
| Points | ? |

## Description

> Don't rush. Letters speak in their own order.
>
> *(Shoshilma. Harflar ham o'z navbati bilan gapiradi.)*

## Solution

The challenge name "Shtaketnik" (fence/paling) and the hint about letter order
points to the **Rail Fence Cipher**.

1. Take the ciphertext from the challenge file
2. Apply Rail Fence decryption (try different rail counts: 2, 3, 4...)
3. The correct number of rails produces readable plaintext containing the flag

**Tools:** CyberChef → "Rail Fence Cipher Decode"

## Flag

`CHC{rail_fence_cipher}`
