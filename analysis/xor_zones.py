#!/usr/bin/env python3
"""Exact XOR sampling zones for UlamInterlace at base=1, ratio=101/100.

Run: python analysis/xor_zones.py

Uses integer arithmetic throughout; no images, prime sieve or dependencies.
A white region is "guaranteed" when XOR vanishes for *every* binary field,
not merely for the particular prime indicator displayed by the web page.
"""
from collections import Counter

P, Q = 101, 100
RADIUS = 50


def sample(x: int, layer: int) -> int:
    """floor(x / (101/100)**layer + 1/2), including negative x."""
    a, b = x * Q**layer, P**layer
    return (2 * a + b) // (2 * b)


def offset_signature(x: int, layers: int) -> tuple[int, ...]:
    """Differences from the unscaled coordinate, layers 1..L-1."""
    return tuple(x - sample(x, j) for j in range(1, layers))


def full_lock(x: int, layers: int) -> bool:
    return all(sample(x, j) == x for j in range(layers))


def pair_lock(x: int, layers: int) -> bool:
    """Adjacent pairs (0,1), (2,3), ... agree in this coordinate."""
    return all(sample(x, j) == sample(x, j+1)
               for j in range(0, layers - layers % 2, 2))


def intervals(values: list[int]) -> list[tuple[int, int]]:
    out = []
    for x in values:
        if not out or x > out[-1][1] + 1:
            out.append([x, x])
        else:
            out[-1][1] = x
    return [tuple(pair) for pair in out]


def first_shift(layer: int, step: int = 0) -> int:
    """First positive x whose offset at this layer becomes step+1."""
    numerator = (2*step + 1) * P**layer
    denominator = 2 * (P**layer - Q**layer)
    return (numerator + denominator - 1) // denominator


def universal_xor_zero(x: int, y: int, layers: int) -> bool:
    """All sampled 2D coordinates occur an even number of times."""
    counts = Counter((sample(x, j), sample(y, j))
                     for j in range(layers))
    return all(n % 2 == 0 for n in counts.values())


def main() -> None:
    print("Base=1 pixel/cell, exact ratio=101/100; coordinates -50..50")
    print("First / second positive offsets by layer:")
    for j in range(1, 6):
        first, second = first_shift(j), first_shift(j, 1)
        assert sample(first-1, j) == first-1
        assert sample(first, j) == first-1
        print(f"  j={j}: first at x={first}, second at x={second}")

    for layers in range(2, 7):
        locked = [x for x in range(-RADIUS, RADIUS+1)
                  if full_lock(x, layers)]
        pairs = [x for x in range(-RADIUS, RADIUS+1)
                 if pair_lock(x, layers)]
        print(f"\nL={layers}: full-lock x={min(locked)}..{max(locked)}")
        print("  Positive-axis offset zones:")
        prev, start = None, 0
        for x in range(RADIUS+2):
            sig = offset_signature(x, layers) if x <= RADIUS else None
            if sig != prev:
                if prev is not None:
                    print(f"    {start:2d}..{x-1:2d}: {prev}")
                prev, start = sig, x
        print("  Pairwise agreement intervals:", intervals(pairs))

        if layers % 2 == 0:
            bands = intervals(pairs)
            # All-field cancellation holds iff every pair of layers samples
            # the same coordinate. Verify independently by multiplicities.
            for x in range(-RADIUS, RADIUS+1):
                for y in range(-RADIUS, RADIUS+1):
                    assert universal_xor_zero(x, y, layers) == (
                        pair_lock(x, layers) and pair_lock(y, layers)
                    )
            print(f"  Guaranteed white: {len(bands)**2} rectangles,"
                  f" {len(pairs)**2} pixels")
        else:
            # Where preceding even number of layers cancel, XOR reduces
            # exactly to the last sampled layer's bit.
            print(f"  Single-last-layer zones: {len(intervals(pairs))**2}"
                  " rectangles (no universally white region)")


if __name__ == "__main__":
    main()
