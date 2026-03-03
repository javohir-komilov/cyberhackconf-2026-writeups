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

# The Curve - Detailed Writeup

## Related Research
- Marco Macchetti, *A Novel Related Nonce Attack for ECDSA* (IACR ePrint 2023/305): https://eprint.iacr.org/2023/305
- Yiming Gao et al., *Attacking ECDSA with Nonce Leakage by Lattice Sieving* (IACR ePrint 2024/296): https://eprint.iacr.org/2024/296
- Jamie Gilchrist et al., *Breaking ECDSA with Two Affinely Related Nonces* (IACR ePrint 2025/705): https://eprint.iacr.org/2025/705

## Problem Model
You are given only:
- secp256k1 public key `(Qx, Qy, n)`
- ordered ECDSA transcript entries `(h_i, r_i, s_i)`

No source is needed for solving.

ECDSA equation per signature:

` s_i = k_i^{-1} (h_i + d r_i) mod n `

So each nonce is affine in private key `d`:

` k_i = h_i/s_i + (r_i/s_i) d mod n `

## Core Weakness
Nonces come from a hidden polynomial recurrence modulo `n`.
This creates algebraic relations across `k_i` values.
Using recurrence elimination, we remove unknown recurrence coefficients and get one univariate polynomial in `d`.

## Elimination Polynomial
Define nonce differences:

` k_{i,j} = k_i - k_j `

Base:

` P(0, j) = k_{j+1,j+2}^2 - k_{j+2,j+3} k_{j,j+1} `

Recurrence:

` P(i, j) = A(i,j) - B(i,j) `

where
- `A(i,j) = P(i-1,j) * Π_{m=1..i+1} k_{j+m, j+i+2}`
- `B(i,j) = P(i-1,j+1) * Π_{m=1..i+1} k_{j, j+m}`

Important implementation detail:
- the product range is `m = 1..i+1` (not `1..i+2`)

After replacing every `k_i` with
`h_i/s_i + (r_i/s_i)d`, we get polynomial `F(d) = 0` over `GF(n)`.

## Recovery Steps
1. Parse `(h_i, r_i, s_i)` from transcript.
2. Build `F(d)` via the recursion above.
3. Find roots of `F` modulo prime `n`.
4. For each root candidate `d*`, check if `d*G == Q`.
5. Encode flag as `CHC{d_as_16_byte_hex}`.

## Provided Solver Scripts
- `organizer/writeup/solve.py`: tested solver using Python + `gp` (`polrootsmod`)
- `organizer/writeup/solve.sage`: Sage variant
- `organizer/writeup/fetch_instance.py`: collect transcript from remote instance

## Solving Static File
From the `organizer/writeup/` folder:

```bash
python3 solve.py --in ../problem/challenge.json --sig-count 11
```

## Solving Remote Instance
1. Fetch transcript:

```bash
python3 fetch_instance.py --host <host> --port 5000 --count 11 --out challenge.json
```

2. Solve:

```bash
python3 solve.py --in challenge.json --sig-count 11
```

## Validation Done
- Elimination polynomial built successfully
- Modular root-finding succeeded
- Recovered `d` matched the organizer secret
- Derived flag format output is correct

## Flag

`CHC{...}` (dynamic per instance — `CHC{d_as_16_byte_hex}`)
