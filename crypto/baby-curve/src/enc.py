#!/usr/bin/env python3

import hashlib
import json
import re
import secrets

from ecdsa.ecdsa import generator_secp256k1

G = generator_secp256k1
N = G.order()
FLAG_RE = re.compile(r"^CHC\{([0-9a-fA-F]{32})\}$")

FAKE_FLAG = "CHC{deadbeefdeadbeefdeadbeefdeadbeef}"


def flag_to_priv(flag: str) -> int:
    m = FLAG_RE.fullmatch(flag)
    if not m:
        raise ValueError("flag must match CHC{<32 hex chars>}")
    d = int(m.group(1), 16)
    if not (1 <= d < N):
        raise ValueError("out of range")
    return d


def inv_mod(x: int, mod: int) -> int:
    return pow(x, -1, mod)


def sign_with_nonce(d: int, msg: bytes, k: int) -> dict:
    z = int.from_bytes(hashlib.sha256(msg).digest(), "big") % N
    r = (k * G).x() % N
    s = (inv_mod(k, N) * (z + r * d)) % N
    return {"h": int(z), "r": int(r), "s": int(s)}


class ToyNonceOracle:
    """Fake nonce source for demonstration only."""

    def __init__(self):
        self.state = secrets.randbelow(N - 1) + 1
        self.coeffs = [
            0x17,
            0x2A,
            0x314159,
            0x271828,
            0xDEADBEEF,
        ]

    def _step(self, x: int) -> int:
        acc = 0
        xp = 1
        for c in self.coeffs:
            acc = (acc + c * xp) % N
            xp = (xp * x) % N
        return acc if acc != 0 else 1

    def next_nonce(self) -> int:
        k = self.state
        self.state = self._step(k)
        return k


def demo() -> None:
    d = flag_to_priv(FAKE_FLAG)
    Q = d * G
    rng = ToyNonceOracle()

    sigs = []
    for i in range(4):
        msg = f"demo::{i}".encode()
        sigs.append(sign_with_nonce(d, msg, rng.next_nonce()))

    out = {
        "public_key": {"n": int(N), "Qx": int(Q.x()), "Qy": int(Q.y())},
        "signatures": sigs,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    demo()
