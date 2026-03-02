#!/usr/bin/env python3
"""Generate a The Curve challenge instance (static attachment mode)."""

import argparse
import json
from pathlib import Path

from core import CurveOracle, DEFAULT_FIXED_FLAG


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="The Curve instance generator")
    parser.add_argument(
        "--public-out",
        default="../problem/challenge.json",
        help="Path for player-facing challenge JSON",
    )
    parser.add_argument(
        "--secret-out",
        default="./_organizer_secret.json",
        help="Path for organizer-only secret JSON",
    )
    parser.add_argument("--sig-count", type=int, default=11, help="Number of signatures to export")
    parser.add_argument("--degree", type=int, default=8, help="Hidden nonce recurrence degree")
    parser.add_argument("--max-queries", type=int, default=64, help="Oracle max signatures for this instance")
    parser.add_argument(
        "--flag",
        default=DEFAULT_FIXED_FLAG,
        help="Fixed flag (format CHC{<32 hex chars>})",
    )
    parser.add_argument("--random-flag", action="store_true", help="Generate a random flag instead of --flag")
    return parser.parse_args()


def build_bundle(oracle: CurveOracle, sig_count: int) -> dict:
    # Keep enough signatures so the intended solve path is feasible.
    min_required = oracle.degree + 3
    if sig_count < min_required:
        raise ValueError(f"sig-count too small (need at least {min_required})")
    if sig_count > oracle.remaining:
        raise ValueError("sig-count exceeds available oracle queries")

    raw = oracle.batch_sign(sig_count, prefix="thecurve")
    signatures = [{"h": int(s["h"]), "r": int(s["r"]), "s": int(s["s"])} for s in raw]
    return {
        "public_key": oracle.pubkey,
        "signatures": signatures,
    }


def main() -> None:
    args = parse_args()
    public_path = Path(args.public_out).resolve()
    secret_path = Path(args.secret_out).resolve()
    public_path.parent.mkdir(parents=True, exist_ok=True)
    secret_path.parent.mkdir(parents=True, exist_ok=True)

    if args.random_flag:
        oracle = CurveOracle.random(degree=args.degree, max_queries=args.max_queries)
    else:
        oracle = CurveOracle.from_flag(args.flag, degree=args.degree, max_queries=args.max_queries)

    public_data = build_bundle(oracle, args.sig_count)
    secret_data = oracle.organizer_snapshot()

    public_path.write_text(json.dumps(public_data, indent=2, default=int))
    secret_path.write_text(json.dumps(secret_data, indent=2, default=int))

    print(f"[+] wrote {public_path}")
    print(f"[+] wrote {secret_path} (private)")
    print(f"[+] signatures = {len(public_data['signatures'])}")
    print(f"[+] flag = {secret_data['flag']}")


if __name__ == "__main__":
    main()
