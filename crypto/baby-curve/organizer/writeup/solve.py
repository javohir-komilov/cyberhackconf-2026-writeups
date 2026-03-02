#!/usr/bin/env python3
"""
The Curve solver (pure Python + PARI/GP).

Requirements:
- python3
- ecdsa Python package
- gp (PARI/GP binary in PATH)
"""

import argparse
import ast
import json
import subprocess
from functools import lru_cache
from pathlib import Path

from ecdsa.ecdsa import generator_secp256k1


def trim(poly):
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def padd(a, b, mod):
    m = max(len(a), len(b))
    out = [0] * m
    for i in range(m):
        ai = a[i] if i < len(a) else 0
        bi = b[i] if i < len(b) else 0
        out[i] = (ai + bi) % mod
    return trim(out)


def psub(a, b, mod):
    m = max(len(a), len(b))
    out = [0] * m
    for i in range(m):
        ai = a[i] if i < len(a) else 0
        bi = b[i] if i < len(b) else 0
        out[i] = (ai - bi) % mod
    return trim(out)


def pmul(a, b, mod):
    out = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj == 0:
                continue
            out[i + j] = (out[i + j] + ai * bj) % mod
    return trim(out)


def build_polynomial(sigs, n):
    rs = [int(s["r"]) % n for s in sigs]
    ss = [int(s["s"]) % n for s in sigs]
    hs = [int(s["h"]) % n for s in sigs]
    inv_ss = [pow(x, -1, n) for x in ss]

    def kdiff(i, j):
        # k_i - k_j = (h_i/s_i - h_j/s_j) + (r_i/s_i - r_j/s_j) * d
        c0 = (hs[i] * inv_ss[i] - hs[j] * inv_ss[j]) % n
        c1 = (rs[i] * inv_ss[i] - rs[j] * inv_ss[j]) % n
        return [c0, c1]

    @lru_cache(None)
    def dpoly(level, start):
        if level == 0:
            return psub(
                pmul(kdiff(start + 1, start + 2), kdiff(start + 1, start + 2), n),
                pmul(kdiff(start + 2, start + 3), kdiff(start, start + 1), n),
                n,
            )

        left = dpoly(level - 1, start)
        # m = 1..level+1
        for m in range(1, level + 2):
            left = pmul(left, kdiff(start + m, start + level + 2), n)

        right = dpoly(level - 1, start + 1)
        for m in range(1, level + 2):
            right = pmul(right, kdiff(start, start + m), n)

        return psub(left, right, n)

    poly = dpoly(len(sigs) - 4, 0)
    inv_lead = pow(poly[-1], -1, n)
    poly = [(c * inv_lead) % n for c in poly]
    return poly


def roots_mod_prime_with_gp(poly, n):
    terms = []
    for i, c in enumerate(poly):
        if c == 0:
            continue
        if i == 0:
            terms.append(f"({c})")
        else:
            terms.append(f"({c})*x^{i}")
    expr = " + ".join(terms) if terms else "0"

    script = f"p={n};f={expr};print(liftall(polrootsmod(f,p)));"
    proc = subprocess.run(["gp", "-q"], input=script.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"gp failed: {proc.stderr.decode(errors='ignore').strip()}")

    out = proc.stdout.decode().strip().replace("~", "")
    if out == "[]":
        return []
    return [int(x) for x in ast.literal_eval(out)]


def solve(path: Path, sig_count: int):
    blob = json.loads(path.read_text())
    pk = blob["public_key"]
    n = int(pk["n"])
    qx = int(pk["Qx"])
    qy = int(pk["Qy"])

    sigs = blob["signatures"]
    if sig_count > 0:
        if len(sigs) < sig_count:
            raise ValueError(f"need at least {sig_count} signatures, got {len(sigs)}")
        sigs = sigs[:sig_count]

    if len(sigs) < 4:
        raise ValueError("need at least 4 signatures")

    poly = build_polynomial(sigs, n)
    roots = roots_mod_prime_with_gp(poly, n)

    G = generator_secp256k1
    found = None
    for cand in roots:
        if not (1 <= cand < n):
            continue
        q = cand * G
        if int(q.x()) == qx and int(q.y()) == qy:
            found = cand
            break

    if found is None:
        raise RuntimeError("no root matched public key")

    if found >= (1 << 128):
        raise RuntimeError("recovered key does not fit CHC{<32 hex>} format")

    flag = f"CHC{{{found.to_bytes(16, 'big').hex()}}}"
    return found, flag, len(poly) - 1, len(roots)


def parse_args():
    parser = argparse.ArgumentParser(description="Solve The Curve from challenge.json")
    parser.add_argument("--in", dest="inp", default="../problem/challenge.json", help="Path to challenge.json")
    parser.add_argument(
        "--sig-count",
        type=int,
        default=11,
        help="Number of first signatures to use (default 11 for current instance design)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    d, flag, deg, roots = solve(Path(args.inp).resolve(), args.sig_count)
    print(f"[+] polynomial degree: {deg}")
    print(f"[+] roots found: {roots}")
    print(f"[+] recovered d: {d}")
    print(f"[+] flag: {flag}")


if __name__ == "__main__":
    main()
