# Ulam Interlace

Several copies of Ulam's prime spiral, each drawn at a different zoom level, all sharing the same centre, woven together pixel by pixel.

**Live:** https://anttiluode.github.io/ulaminterlace/

One self-contained HTML file (`index.html`). No libraries, no build step. Open it in a browser.

![Screenshot](screenshot.jpg)

## What it does

The Ulam spiral writes the integers outward from the centre in a square spiral (1 at the centre, 2 to the right, then counter-clockwise) and lights the primes. Primes cluster on diagonals, because each diagonal is a quadratic polynomial in the ring index.

This tool draws 1 to 6 copies of that spiral. Layer *i* has cell size

```
z_i = base · ratio^i        (pixels per integer)
```

and every layer puts the integer at the centre on the same screen point. The layers are then combined in one of eight ways.

**Interlace** (each pixel shows exactly one layer):

| Mode | Pixel belongs to layer |
|---|---|
| Rows | `floor(dy / band) mod L` |
| Columns | `floor(dx / band) mod L` |
| Checker | `floor(dx / band) + floor(dy / band) mod L` |
| Square rings | `floor(max(|dx|, |dy|) / band) mod L` — the spiral's own shells |
| Round rings | `floor(hypot(dx, dy) / band) mod L` |

`dx, dy` are measured from the shared centre, so the weave stays fixed to the spiral when you pan.

**Blend** (every layer contributes to every pixel), with each layer's value `v_i` in [0, 1]:

| Mode | Value |
|---|---|
| Overlay | dark theme: additive light, `Σ v_i · colour_i`; light theme: inks, `paper · Π (1 − v_i(1 − colour_i))` |
| XOR | `(1 − Π (1 − 2 v_i)) / 2` — for binary values, lit where an odd number of layers have a prime |
| Coincide | `Π v_i` — lit only where every layer has a prime |

The dark theme uses red, green and blue lights; the light theme uses cyan, magenta and yellow inks, so overlaps mix the way they would on a screen or on paper.

## About the horizontal lines

In **Rows** mode the horizontal stripes are the weave itself: each band of `band` pixel rows is taken from the next layer in turn, so you see layer 1's spiral through one stripe, layer 2's through the next, and so on. Each stripe is a window onto a spiral at a different scale. Raise the band width to see more of each layer per stripe, or switch to Square rings or Round rings to weave by distance from the centre instead.

When the cell size is fractional (say 1.18 px per integer), nearest-neighbour sampling repeats some pixel rows and columns, which adds a fine, regular beat of its own on top.

## Zoomed out: density shading

Below 1 pixel per integer, one pixel covers several integers. Instead of picking one, the pixel shows

```
v = min(1, ½ · (primes in block / integers in block) · ln n)
```

The prime number theorem says primes thin out like `1 / ln n`, so multiplying by `ln n` cancels that drift and keeps the diagonals visible at large n instead of everything fading to grey.

## Other controls

- **Centre number.** The integer placed at the centre. Start at 41 and Euler's `n² + n + 41` shows up as one long unbroken diagonal of primes (it produces primes for n = 0 to 39).
- **Ratio presets.** √2, φ, 2, 3. Rational ratios line the layers' diagonals up periodically; φ and √2 do not, which gives a different moiré.
- **Layer chips.** Click to mute a layer.
- **Readout.** Hovering shows, for every layer, the cell position, the integer n there, and whether it is prime. In interlace modes the row for the layer that owns that pixel is highlighted.
- **Sweep zoom** animates the base cell size back and forth.
- Drag to pan, scroll or press `+` / `−` to zoom around the cursor, arrow keys pan.

## Limits

- Primes come from a sieve of Eratosthenes that grows as needed, capped at 2²⁵ = 33,554,432. Integers above that are not sieved and draw blank; the status line says when that happens.
- Rendering is plain JavaScript into an `ImageData` buffer on the CPU. The canvas is at most 820 × 820 pixels. Far-zoomed-out views with many layers take longer per frame because each pixel sums over a block of integers.

## Spiral indexing

Ring *k* (Chebyshev distance *k* from the centre) holds the integers from `(2k−1)² + 1` to `(2k+1)²`. With `b = (2k−1)²`:

```
right side  x = k,  y > −k :  n = b + y + k
top         y = k         :  n = b + 2k + (k − x)
left        x = −k        :  n = b + 4k + (k − y)
bottom      y = −k        :  n = b + 6k + (x + k)
```

Then `n = index + start − 1` when the centre number is changed.
