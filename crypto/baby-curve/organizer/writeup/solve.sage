#!/usr/bin/env sage

import json
from functools import lru_cache
from pathlib import Path

from ecdsa.ecdsa import generator_secp256k1

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "problem" / "challenge.json"

blob = json.loads(DATA.read_text())
pk = blob["public_key"]
sigs = blob["signatures"]
need = int(blob.get("required_min_signatures", len(sigs)))
if need > len(sigs):
    raise ValueError("challenge.json requires more signatures than provided")
if len(sigs) != need:
    sigs = sigs[:need]

n = int(pk["n"])
Qx = int(pk["Qx"])
Qy = int(pk["Qy"])

if len(sigs) < 4:
    raise ValueError("Need at least 4 signatures")

F = GF(n)
R.<d> = PolynomialRing(F)

rs = [F(int(s["r"])) for s in sigs]
ss = [F(int(s["s"])) for s in sigs]
hs = [F(int(s["h"])) for s in sigs]
inv_ss = [x**(-1) for x in ss]


def kdiff(i, j):
    """k_i - k_j expressed as affine polynomial in d."""
    c0 = hs[i] * inv_ss[i] - hs[j] * inv_ss[j]
    c1 = rs[i] * inv_ss[i] - rs[j] * inv_ss[j]
    return c0 + c1 * d


@lru_cache(None)
def dpoly(level, start):
    """
    Recurrence-elimination polynomial over nonce differences.
    Equivalent to dpoly(N-4, 0) from the paper's recursive construction.
    """
    if level == 0:
        return kdiff(start + 1, start + 2) ** 2 - kdiff(start + 2, start + 3) * kdiff(start, start + 1)

    left = dpoly(level - 1, start)
    # Important: use level+1 factors (m = 1..level+1), not level+2.
    for m in range(1, level + 2):
        left *= kdiff(start + m, start + level + 2)

    right = dpoly(level - 1, start + 1)
    for m in range(1, level + 2):
        right *= kdiff(start, start + m)

    return left - right


N = len(sigs)
poly = dpoly(N - 4, 0)
poly = poly.monic()

roots = [int(rt) for (rt, _mult) in poly.roots()]
if not roots:
    raise RuntimeError("No roots found - instance might be malformed")

G = generator_secp256k1

found = None
for cand in roots:
    if not (1 <= cand < n):
        continue
    Q = cand * G
    if int(Q.x()) == Qx and int(Q.y()) == Qy:
        found = cand
        break

if found is None:
    raise RuntimeError("No root matched the public key")

if found >= (1 << 128):
    raise RuntimeError("Recovered key does not match challenge flag encoding")

flag = f"CHC{{{found.to_bytes(16, 'big').hex()}}}"
print(f"[+] recovered d = {found}")
print(f"[+] flag = {flag}")
