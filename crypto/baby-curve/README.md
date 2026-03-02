# Baby Curve

| Field | Value |
|-------|-------|
| Category | Crypto |
| Points | 500 |

## Description

> Our baby curve had one job — protect the flag.
> The encryption scheme uses elliptic curve signatures. You are given a set of
> signatures and the encrypted flag. The signing oracle lets you query additional
> signatures (up to 64), with the same secret key and a biased nonce.

## Solution

The challenge implements ECDSA over a custom curve with a biased nonce.
Given enough signatures with a known nonce bias, the secret key can be
recovered using the **Lattice-based Hidden Number Problem (HNP)** approach.

**Attack summary:**
1. Collect 11 pre-generated signatures from `challenge.json`
2. Query up to 64 more from the live oracle (optional)
3. Build an HNP lattice from the signature equations:
   - Each signature satisfies: `s·k = h + r·d (mod n)`, where the high bits of `k` are 0
4. Use LLL/BKZ lattice reduction (via SageMath `sage solve.sage`)
5. Recover secret key `d` → decrypt the flag

**Tools:** SageMath, Python 3

See `organizer/` for the full solve script and generator.

## Flag

`CHC{...}` (dynamic per instance)
