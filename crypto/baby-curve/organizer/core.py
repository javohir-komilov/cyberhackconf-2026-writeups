#!/usr/bin/env python3
"""Core logic for The Curve related-nonce ECDSA challenge."""

import hashlib
import re
import secrets
from dataclasses import dataclass

from ecdsa.ecdsa import generator_secp256k1

CURVE_NAME = "secp256k1"
G = generator_secp256k1
N = G.order()
FLAG_RE = re.compile(r"^CHC\{([0-9a-fA-F]{32})\}$")
DEFAULT_FIXED_FLAG = "CHC{00112233445566778899aabbccddeeff}"


def inv_mod(x: int, mod: int) -> int:
    return pow(x, -1, mod)


def eval_poly(coeffs: list[int], x: int, mod: int) -> int:
    acc = 0
    xp = 1
    for c in coeffs:
        acc = (acc + c * xp) % mod
        xp = (xp * x) % mod
    return acc


def parse_flag_to_d(flag: str) -> int:
    m = FLAG_RE.fullmatch(flag.strip())
    if not m:
        raise ValueError("FLAG must be CHC{<32 hex chars>}")
    d = int(m.group(1), 16)
    if not (1 <= d < N):
        raise ValueError("FLAG-embedded key is out of secp256k1 order range")
    return d


def d_to_flag(d: int) -> str:
    if not (1 <= d < (1 << 128)):
        raise ValueError("d must fit in 128 bits for CHC{...} flag encoding")
    return f"CHC{{{d.to_bytes(16, 'big').hex()}}}"


def _is_nonce_chain_valid(k0: int, coeffs: list[int], horizon: int) -> bool:
    k = k0
    for _ in range(horizon):
        if k == 0:
            return False
        r = (k * G).x() % N
        if r == 0:
            return False
        k = eval_poly(coeffs, k, N)
    return True


def _random_params(degree: int, horizon: int) -> tuple[list[int], int]:
    if degree < 1:
        raise ValueError("degree must be >= 1")

    while True:
        coeffs = [secrets.randbelow(N) for _ in range(degree + 1)]
        if coeffs[-1] == 0:
            continue

        k0 = secrets.randbelow(N - 1) + 1
        if _is_nonce_chain_valid(k0, coeffs, horizon):
            return coeffs, k0


@dataclass
class CurveOracle:
    d: int
    coeffs: list[int]
    nonce_state: int
    max_queries: int
    queries_used: int = 0

    @property
    def degree(self) -> int:
        return len(self.coeffs) - 1

    @property
    def flag(self) -> str:
        return d_to_flag(self.d)

    @property
    def remaining(self) -> int:
        return self.max_queries - self.queries_used

    @property
    def pubkey(self) -> dict:
        q = self.d * G
        return {
            "n": int(N),
            "Qx": int(q.x()),
            "Qy": int(q.y()),
        }

    @classmethod
    def random(cls, degree: int = 8, max_queries: int = 48):
        if max_queries < 4:
            raise ValueError("max_queries must be >= 4")

        while True:
            d = int.from_bytes(secrets.token_bytes(16), "big")
            if 1 <= d < N:
                break

        coeffs, k0 = _random_params(degree, max_queries + 64)
        return cls(d=d, coeffs=coeffs, nonce_state=k0, max_queries=max_queries)

    @classmethod
    def from_flag(cls, flag: str, degree: int = 8, max_queries: int = 48):
        d = parse_flag_to_d(flag)
        coeffs, k0 = _random_params(degree, max_queries + 64)
        return cls(d=d, coeffs=coeffs, nonce_state=k0, max_queries=max_queries)

    def _next_nonce(self) -> int:
        if self.queries_used >= self.max_queries:
            raise ValueError("query limit reached")

        k = self.nonce_state
        self.nonce_state = eval_poly(self.coeffs, k, N)
        self.queries_used += 1
        if k == 0:
            raise ValueError("internal nonce became zero")
        return k

    def sign(self, message: bytes) -> dict:
        if not isinstance(message, (bytes, bytearray)):
            raise TypeError("message must be bytes")

        k = self._next_nonce()
        z = int.from_bytes(hashlib.sha256(message).digest(), "big") % N
        r = (k * G).x() % N
        if r == 0:
            raise ValueError("invalid r=0")

        s = (inv_mod(k, N) * (z + r * self.d)) % N
        if s == 0:
            raise ValueError("invalid s=0")

        return {
            "idx": self.queries_used - 1,
            "msg": message.decode(errors="replace"),
            "h": int(z),
            "r": int(r),
            "s": int(s),
        }

    def batch_sign(self, count: int, prefix: str = "thecurve") -> list[dict]:
        if count < 1:
            raise ValueError("count must be positive")
        out = []
        for _ in range(count):
            msg = f"{prefix}::{self.queries_used:04d}".encode()
            out.append(self.sign(msg))
        return out

    def public_snapshot(self) -> dict:
        return {
            "challenge": "The Curve",
            "description": "secp256k1 ECDSA signing transcript",
            "public_key": self.pubkey,
        }

    def organizer_snapshot(self) -> dict:
        return {
            "flag": self.flag,
            "privkey_d": int(self.d),
            "degree": int(self.degree),
            "coeffs": [int(c) for c in self.coeffs],
            "current_nonce_state": int(self.nonce_state),
            "queries_used": int(self.queries_used),
            "max_queries": int(self.max_queries),
        }
