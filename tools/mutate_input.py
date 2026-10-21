#!/usr/bin/env python3
"""Generic datagram mutator for network testing.

This tool only applies coarse, non-targeted mutations (bit flips, truncation,
and padding). It is not a vulnerability-specific generator.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from coap_client import load_datagram, sha256_hex, write_bytes


def mutate(
    data: bytes,
    seed: int,
    flips: int,
    truncate: int,
    pad: int,
) -> bytes:
    """Return a mutated copy of *data*.

    Args:
        data: Original datagram.
        seed: RNG seed for repeatable mutations.
        flips: Number of random byte substitutions.
        truncate: Bytes to remove from the end, if available.
        pad: Number of zero bytes to append.

    Returns:
        Mutated datagram. Empty input stays empty except for padding.
    """
    rng = random.Random(seed)
    mutated = bytearray(data)
    if truncate > 0:
        keep = max(0, len(mutated) - truncate)
        mutated = mutated[:keep]
    for _ in range(max(0, flips)):
        if not mutated:
            break
        index = rng.randrange(len(mutated))
        mutated[index] = rng.randrange(256)
    if pad > 0:
        mutated.extend(b"\x00" * pad)
    return bytes(mutated)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Mutate a saved CoAP/UDP datagram."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--flips", type=int, default=1)
    parser.add_argument("--truncate", type=int, default=0)
    parser.add_argument("--pad", type=int, default=0)
    args = parser.parse_args(argv)

    try:
        original = load_datagram(args.input)
        mutated = mutate(
            original, args.seed, args.flips, args.truncate, args.pad
        )
        write_bytes(args.output, mutated)
        print(
            f"wrote {args.output} len={len(mutated)} "
            f"sha256={sha256_hex(mutated)}"
        )
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
