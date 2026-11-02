# Ulam Interlace

Several copies of Ulam's prime spiral, each drawn at a different zoom level, all sharing the same centre, woven together pixel by pixel.

**Live:** https://anttiluode.github.io/ulaminterlace/

One self-contained HTML file (`index.html`). No libraries, no build step. Open it in a browser.

| Rows, 4 layers, ratio ×1.64 | Square rings, 4 layers, ratio ×2.60 |
|---|---|
| ![Rows weave](screenshot.jpg) | ![Square rings weave](screenshot_rings.jpg) |

The [Analysis](#analysis) section below measures what the picture is made of: every straight line of the spiral is a quadratic polynomial, its brightness is predicted by the Hardy–Littlewood constant to within a few percent, and the horizontal streaks come from rows that are themselves quadratics.

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

Three things make horizontal lines in **Rows** mode:

1. **The weave.** Each band of `band` pixel rows is taken from the next layer in turn, so the colour stripes are windows onto spirals at different scales.
2. **The rows themselves.** Outside the cone |x| < |y|, a row of the Ulam spiral is a quadratic polynomial, and different rows hold very different numbers of primes (measured: 22 to 309 primes in equal 1801-cell segments). So the bands also change brightness from row to row. See [Why rows streak](#3-why-rows-streak).
3. **Sampling.** At fractional cell sizes (say 1.18 px per integer), nearest-neighbour sampling repeats some pixel rows, which adds a fine regular beat.

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

---

## Analysis

`analysis/analyze.py` reimplements the page's spiral indexing and its exact pixel-to-cell sampling in numpy, sieves to 1.2 × 10⁸, and measures the system. It runs in about 12 seconds and writes `analysis/results.json` plus the two figures below. Every number in this section comes from that file.

```
python analysis/analyze.py
```

### 1. Parity law

**n ≡ x + y + 1 (mod 2)** at every cell.

The spiral is a walk on the square lattice with unit steps. Each step changes n by 1 and changes x + y by ±1, so the parities of n and x + y flip together, starting from n = 1 at (0, 0). Consequence: every odd prime sits on the cells with x + y even, one colour of a checkerboard. Checked on all 3001 × 3001 cells around the centre.

### 2. Every straight line is a quadratic, and its brightness is predictable

Far enough from the centre, every step along a diagonal, row or column crosses exactly one shell of the spiral. Shell k ends at (2k + 1)², so along any such ray

```
n(s) = 4s² + B·s + C        (exact, integer coefficients)
```

This was verified exactly for 2,408 rays (8 directions × offsets −150…150, s up to 5,000).

The parity of B decides how the ray looks:

| Ray | B | Consequence |
|---|---|---|
| diagonal (NE, SW, NW, SE) | always even | f(s) mod 2 is constant: the whole ray is odd or the whole ray is even |
| row east / west | −3 / +1 | parity alternates along the ray |
| column north / south | −1 / +3 | parity alternates along the ray |

That is why the diagonals dominate the picture. Half of all diagonals are entirely even and carry no primes at all (563 rays, 0 primes found), and the other half carry odd numbers only, at twice the average density.

**Hardy–Littlewood.** For an irreducible f, the conjectured number of primes among f(s₀), …, f(S) is

```
           S                                            1 − ω_f(p)/p
  C(f) ·   Σ   1 / ln f(s),        C(f) =   ∏ (p prime) ──────────────
          s=s₀                                           1 − 1/p
```

where ω_f(p) counts the roots of f mod p. A small prime p that never divides f(s) raises C; one that divides f often lowers it. The script computes C over primes up to 20,000 and compares with the counted primes on every ray:

| Rays | Count | Pearson r (observed vs predicted) | observed / predicted, median | 5–95 % range | C(f) range among live rays |
|---|---|---|---|---|---|
| diagonals | 1,204 | 0.999 | 1.002 | 0.95 – 1.04 | 0.62 – 6.65 |
| rows and columns | 1,204 | 0.998 | 1.001 | 0.94 – 1.07 | 0.33 – 3.27 |

![Rays vs Hardy-Littlewood](analysis/rays_vs_hardy_littlewood.png)

C(f) is the brightness of a line. It varies more than tenfold between diagonals, which is the contrast you see between bright and faint diagonal streaks.

| Ray | f(s) | C(f) | primes counted | predicted |
|---|---|---|---|---|
| richest (line x − y = −40, NE) | 4s² − 2s + 41 | 6.65 | 2,028 | 2,027.6 |
| same line, SW ray | 4s² + 2s + 41 | 6.65 | 2,047 | 2,027.4 |
| SE ray of x + y = 58 | 4s² + 460s + 13283 | 5.93 | 1,782 | 1,782.6 |
| poorest live (x − y = −74, NE) | 4s² − 2s + 75 | 0.62 | 193 | 187.4 |

The richest line is the Euler family: 4s² ± 2s + 41 is n² + n + 41 at n = ±2s.

**Empty odd lines.** Some odd diagonals are also completely empty, because f factors. Two families on the anti-diagonal direction:

```
SE ray of x + y = −m²      (m even):  f = (2s + 1)² − m² = (2s + 1 − m)(2s + 1 + m)
NW ray of x + y = 1 + m²   (m odd):   f = 4s² − m²       = (2s − m)(2s + m)
```

m = 0 is the SE main diagonal, which is exactly the odd squares. Across all rays, 98 are reducible and they hold 0 primes.

### 3. Why rows streak

A row y = Y crosses two regions.

- **Inside the cone |x| < |y|**, the row runs along the top or bottom side of one shell, so it reads consecutive integers. Nothing arithmetic changes from one row to the next.
- **Outside the cone |x| > |y|**, the row crosses one shell per cell and reads the quadratic `4s² − 3s + (1 + Y)` (east) or `4s² + s + (1 − Y)` (west). Its density is set by C(f), which changes with Y.

Measured on rows 1000–1300, with equal 1801-cell segments of each row:

| Segment | mean primes | row-to-row sd | sd if primes were random | ratio |
|---|---|---|---|---|
| outside the cone, x = 1400…3200 | 107 | 59.3 | 10.0 | **5.9×** |
| inside the cone, x = −900…900 | 117 | 7.2 | 10.4 | 0.69× |

Outside the cone, the row counts range from 22 to 309 and correlate with the row's Hardy–Littlewood constant at r = 0.993.

![Row streaks](analysis/row_streaks.png)

So the horizontal streaks are real arithmetic, and they live in the left and right wedges of the plate. The top and bottom wedges carry the same effect turned 90°: vertical streaks from the columns.

Inside the cone the counts vary *less* than random. That is the known behaviour of primes in short intervals of consecutive integers: Montgomery and Soundararajan's formula gives a ratio of about 0.6 at these sizes. The script does not test that formula beyond this one comparison.

### 4. Square rings are one spiral with a stepped zoom

Chebyshev rings around the centre are exactly the shells of the spiral. In Square rings mode, a pixel at Chebyshev radius d that belongs to layer i shows shell k = d / zᵢ, so the integers it shows are about

```
n ≈ 4 d² / zᵢ²
```

The whole picture is therefore a single spiral whose zoom is a step function of radius.

- The four main diagonal rays pass through the shared centre. Scaling about the centre maps them to themselves, so they run unbroken across every ring boundary.
- An off-centre diagonal x − y = c sits at pixel offset c·zᵢ, so it jumps sideways by c·(zⱼ − zᵢ) where layer i meets layer j.

In the second screenshot the four layers have z = 0.294, 0.763, 1.98 and 5.14 px per cell. At d = 100 px they show integers near 464,000, 68,700, 10,200 and 1,500. The ratio between the outer two layers is 2.598⁶ ≈ 307. Each ring is a window onto a different range of the number line, at a scale where its diagonals still line up with those in the other rings.

### 5. Coincide and XOR: what links two layers

Coincide lights a pixel only where both layers have a prime. With layer A at 1 px per cell and layer B at ratio r, over 1201 × 1201 pixels:

| r | P(A prime) | P(B prime) | P(both) | lift = P(both) / (P(A) P(B)) | parity-only lift | lift from 2, 3, 5 | residual | XOR lit |
|---|---|---|---|---|---|---|---|---|
| 1.25 | 0.076 | 0.082 | 0.0066 | 1.045 | 1.00 | 1.034 | 1.010 | 14.5 % |
| √2 | 0.076 | 0.080 | 0.0062 | 1.014 | 1.00 | 1.000 | 1.015 | 14.4 % |
| 1.5 | 0.076 | 0.090 | 0.0074 | 1.069 | 1.00 | 1.060 | 1.009 | 15.2 % |
| φ | 0.076 | 0.082 | 0.0062 | 0.992 | 1.00 | 0.999 | 0.993 | 14.6 % |
| 2 | 0.076 | 0.085 | 0.0057 | **0.867** | 1.00 | 0.883 | 0.982 | 15.0 % |
| e | 0.076 | 0.090 | 0.0069 | 0.996 | 1.00 | 0.999 | 0.997 | 15.3 % |
| 3 | 0.076 | 0.092 | 0.0079 | **1.124** | 1.11 | 1.135 | 0.990 | 15.2 % |
| 4 | 0.076 | 0.097 | 0.0077 | 1.039 | 1.00 | 1.028 | 1.011 | 15.8 % |

"Lift from 2, 3, 5" is the same lift computed for "coprime to 30" instead of "prime". The residual is what is left after dividing it out.

- The two layers are close to independent. Coincide shows about the product of two prime densities, around 0.6 % of pixels.
- Every deviation larger than 1.5 % is explained by divisibility by 2, 3 and 5 alone.
- **Ratio 3 lifts by 12 %**, mostly through parity. A fine cell at x = 3X has x + y ≡ X + Y (mod 2), so both layers sit on the same checkerboard colour.
- **Ratio 2 suppresses by 13 %**. Parity is neutral here, because x = 2X makes x + y even whatever the coarse cell is. The suppression comes from residues mod 3 and 5.
- Irrational ratios (φ, e) give lift ≈ 1. That is the "nothing aligns" case: the moiré you see at these ratios is geometry, not arithmetic.

### 6. Shared primes on the main diagonals

For an integer ratio r, the pixel at (rm, rm) on a main diagonal shows f(rm) in the fine layer and f(m) in the coarse one. So Coincide along that diagonal asks for both f(m) and f(rm) to be prime. The two-polynomial Bateman–Horn conjecture predicts

```
   M                                       1 − ω_{fg}(p)/p
C₂ Σ  1 / (ln f(m) · ln g(m)),     C₂ = ∏ ─────────────────,    g(m) = f(rm)
  m=1                                       (1 − 1/p)²
```

Measured for m ≤ 1500:

| Diagonal | f(s) | r | both prime | predicted | C₂ |
|---|---|---|---|---|---|
| NE | 4s² − 2s + 1 | 2 | 29 | 31.8 | 3.96 |
| NE | 4s² − 2s + 1 | 3 | 43 | 49.5 | 6.59 |
| NW | 4s² + 1 | 2 | 25 | 30.6 | 3.88 |
| NW | 4s² + 1 | 3 | 32 | 28.7 | 3.88 |
| SW | 4s² + 2s + 1 | 2 | 25 | 30.9 | 3.96 |
| SW | 4s² + 2s + 1 | 3 | 46 | 48.4 | 6.59 |

In total 200 shared primes were observed against 220 predicted (0.91). That is within about 1.4 standard deviations of a Poisson count, and the conjecture is asymptotic while these values are small.

The constant differs between ratios. On the NE and SW diagonals it is 6.59 at ratio 3 and 3.96 at ratio 2, so a ratio-3 overlay shares about 1.6 times as many primes along those diagonals.

### 7. Density shading below 1 px per cell

Shaded value v = min(1, ½ · (primes / cells) · ln n), measured on the page's exact sampling footprint:

| Cell size z | Area ratio 1/z² | Cells sampled per axis | mean v across radius bins | pixels clipped at v = 1 |
|---|---|---|---|---|
| 0.5 | 4 | 3 | 0.456 – 0.480 | 14 – 22 % |
| 0.25 | 16 | 5 | 0.499 – 0.509 | 6 – 9 % |
| 0.1 | 100 | 11 | 0.511 | ≤ 0.3 % |

The ln n factor does its job. The mean stays flat while n grows from about 5 × 10⁴ to 3 × 10⁷, so the plate does not fade with distance.

Clipping is high at z = 0.5, where each pixel averages only a few cells.

A pixel samples every cell it touches, so neighbouring pixels share one edge row of cells. In effect that is a one-cell blur. The readout's "cells per px" reports the area ratio 1/z², not the sampled count.

### 8. The Euler line

With centre number 41, the line x − y = 0 through the centre carries 40 consecutive primes. These are n² + n + 41 for n = 0…39, split between the two rays. Within 60 cells of the centre, 85 % of that line is prime. The next best line has a run of 8.

### Ledger

**Verified exactly**
- the parity law
- that every ray beyond the central cross is an exact quadratic
- that reducible and even rays hold no primes in range

**Measured, within the computed range**
- Hardy–Littlewood and Bateman–Horn agreement (both are conjectures; these are consistency checks, not proofs)
- the row-streak variance
- the layer lifts
- the shading calibration

**Not established here**
- the Montgomery–Soundararajan comparison, beyond one number
- anything new in number theory: the arithmetic of Ulam diagonals is classical (Hardy & Littlewood 1923, Bateman & Horn 1962)

What is specific to this tool is how its weaves select from that arithmetic:
- rows sample the quadratic rows of the spiral
- square rings stack shells from different integer ranges
- Coincide at integer ratios pairs f(m) with f(rm)
