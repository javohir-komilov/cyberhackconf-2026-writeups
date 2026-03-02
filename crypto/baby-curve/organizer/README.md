# The Curve

## Category
Crypto (Hard)

## Flag format
`CHC{<32 hex chars>}`

## Public data
`challenge.json` contains:
- public key (`Qx`, `Qy`, `n`) on `secp256k1`
- signature entries (`h`, `r`, `s`)

## Objective
Recover the signing private key and submit the flag.

## Instance generation (organizer)
```bash
python3 enc.py --public-out ../problem/challenge.json --secret-out ./_organizer_secret.json --sig-count 11 --max-queries 64
```

## Fixed flag (default)
`CHC{00112233445566778899aabbccddeeff}`
