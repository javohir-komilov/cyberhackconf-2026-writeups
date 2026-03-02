# Signaling in Headers

| Field | Value |
|-------|-------|
| Category | Misc |
| Points | ? |

## Description

> (Challenge description unavailable — provided to players via CTFd.)

## Solution

*See [`src/Misc/writeup.md`](src/Misc/writeup.md) for the full solution (in Uzbek).*

**Vulnerability chain:** HTTP Response Header Analysis → Multi-layer Encoding → Hidden Endpoints

**Summary:**
1. Visit `/robots.txt` → finds `/hints/*` and `/api/ping`
2. `GET /api/ping` → response contains `X-CTF` header with 3-layer encoded path
3. Decode: **base64 → hex → ROT13** → reveals `/internal/door`
4. `/internal/door` → `PREFIX_B64` (base64-encoded password prefix)
5. `/internal/k1` → base64 → reverse → key part 1
6. `/internal/k2` → hex → ASCII → key part 2
7. Assemble: `PREFIX + k1 + k2` = admin password
8. `POST /login?u=admin` with password → access `/flag`

```bash
# Decode the X-CTF header (replace with actual value):
echo 'PASTE_X_CTF_HERE' | base64 -d | xxd -r -p | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

## Flag

`CHC{...}`
