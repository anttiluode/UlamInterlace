"""
Analysis of the Ulam Interlace system.

Reproduces the page's exact spiral indexing and pixel->cell sampling in numpy,
then measures:

  1. the parity law  n = x + y + 1 (mod 2)
  2. every straight ray of the spiral as a quadratic polynomial 4s^2 + Bs + C,
     and its prime count against the Hardy-Littlewood (Bateman-Horn) prediction
  3. why rows of the plate streak: row-to-row variance inside vs outside the cone
  4. layer coincidence (the page's Coincide / XOR modes): lift over independence,
     and how much of it the parity law explains
  5. paired-polynomial check: primes shared by two layers on a main diagonal
     against the two-polynomial Bateman-Horn constant
  6. calibration of the density shading below 1 px per cell
  7. the Euler line at centre number 41
  8. ratio sweep: coincidence lift as a function of the ratio r in [1, 4],
     and which small primes carry the resonances at fractions p/q
  9. Checker weave at 1 px band: a layer at exactly 1 px per cell with an
     odd slot index and an even layer count can show no odd number at all

Run:  python analysis/analyze.py      (about a minute, ~1 GB RAM)
Writes analysis/results.json and analysis/*.png
"""
import json, math, os, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
t_start = time.time()
R = {}

# ---------------------------------------------------------------- primes
NMAX = 120_000_000
def sieve(n):
    s = np.ones(n + 1, dtype=bool); s[:2] = False; s[4::2] = False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if s[i]: s[i*i::2*i] = False
    return s
PR = sieve(NMAX)
def isprime(n):
    n = np.asarray(n, dtype=np.int64)
    out = np.zeros(n.shape, dtype=bool)
    ok = (n >= 0) & (n <= NMAX)
    out[ok] = PR[n[ok]]
    return out
SMALLP = np.flatnonzero(sieve(20000))

# ---------------------------------------------------------------- spiral (same as the page)
def idx(x, y):
    x = np.asarray(x, dtype=np.int64); y = np.asarray(y, dtype=np.int64)
    k = np.maximum(np.abs(x), np.abs(y)); b = (2*k - 1)**2
    n = np.where((x == k) & (y > -k), b + y + k,
        np.where(y == k, b + 2*k + (k - x),
        np.where(x == -k, b + 4*k + (k - y), b + 6*k + (x + k))))
    return np.where(k == 0, 1, n)

# ---------------------------------------------------------------- 1. parity law
G = 1500
gx, gy = np.meshgrid(np.arange(-G, G+1), np.arange(-G, G+1))
gn = idx(gx, gy)
assert len(np.unique(gn)) == gn.size and gn.min() == 1 and gn.max() == (2*G+1)**2
parity_ok = bool(np.all((gn % 2) == ((gx + gy + 1) % 2)))
odd_primes_on_even_sum = bool(np.all(((gx + gy) % 2 == 0) | ~isprime(gn) | (gn == 2)))
R["parity"] = {"grid": f"{2*G+1}x{2*G+1}", "n_equiv_x_plus_y_plus_1_mod_2": parity_ok,
               "all_odd_primes_on_even_x_plus_y": odd_primes_on_even_sum}
print("1. parity law holds:", parity_ok, odd_primes_on_even_sum)
del gx, gy, gn

# ---------------------------------------------------------------- 2. rays as quadratics
def ray_points(kind, c, s):
    if kind == "NE": return s + c, s          # line x - y = c, t -> +inf
    if kind == "SW": return -s + c, -s        # line x - y = c, t -> -inf
    if kind == "NW": return c - s, s          # line x + y = c, t -> +inf
    if kind == "SE": return c + s, -s         # line x + y = c, t -> -inf
    if kind == "E":  return s, np.full_like(s, c)   # row y = c
    if kind == "W":  return -s, np.full_like(s, c)
    if kind == "N":  return np.full_like(s, c), s   # column x = c
    if kind == "S":  return np.full_like(s, c), -s
KINDS_DIAG = ["NE", "SW", "NW", "SE"]; KINDS_AXIS = ["E", "W", "N", "S"]

def fit_quadratic(s, n):
    # exact integer fit from three far points, then verify on the whole ray
    s3 = s[[0, 1, 2]].astype(object); n3 = n[[0, 1, 2]].astype(object)
    d2 = n3[2] - 2*n3[1] + n3[0]; A = d2 // 2
    B = (n3[1] - n3[0]) - A*(2*s3[0] + 1)
    C = n3[0] - A*s3[0]**2 - B*s3[0]
    ok = np.array_equal(A*s.astype(np.int64)**2 + B*s.astype(np.int64) + C, n)
    return int(A), int(B), int(C), ok

def legendre_vec(D, p):
    # D: int64 array, returns Legendre symbol (D/p) for odd prime p
    a = np.mod(D, p).astype(np.int64); e = (p - 1)//2; r = np.ones_like(a)
    while e:
        if e & 1: r = (r * a) % p
        a = (a * a) % p; e >>= 1
    return np.where(r == p - 1, -1, r)

def hl_constants(A, B, C):
    """Hardy-Littlewood / Bateman-Horn constant prod_p (1 - w(p)/p)/(1 - 1/p)
    for f(s) = A s^2 + B s + C (A = 4), arrays of B, C. Primes up to 20000."""
    A = np.asarray(A, np.int64); B = np.asarray(B, np.int64); C = np.asarray(C, np.int64)
    logc = np.zeros(len(B))
    for p in SMALLP:
        p = int(p)
        if p < 50:
            s = np.arange(p)
            w = ((A[:, None]*s*s + B[:, None]*s + C[:, None]) % p == 0).sum(1)
        else:
            D = B*B - 4*A*C
            w = 1 + legendre_vec(D, p)
            w = np.where(np.mod(D, p) == 0, 1, w)
        with np.errstate(divide="ignore"):
            logc += np.log(np.maximum(1 - w/p, 0)) - math.log(1 - 1/p)
    return np.exp(logc)

def is_square(v):
    v = int(v)
    return v >= 0 and math.isqrt(v)**2 == v

S_MAX, CR = 5000, 150
rays = []
for kind in KINDS_DIAG + KINDS_AXIS:
    for c in range(-CR, CR + 1):
        s = np.arange(abs(c) + 2, S_MAX + 1, dtype=np.int64)
        x, y = ray_points(kind, c, s)
        n = idx(x, y)
        A, B, C, ok = fit_quadratic(s, n)
        assert ok, (kind, c)
        pm = isprime(n)
        # expected count without the arithmetic constant: sum 1/ln f
        base = float(np.sum(1.0/np.log(np.maximum(n, 3).astype(np.float64))))
        rays.append(dict(kind=kind, c=c, A=A, B=B, C=C, s0=int(s[0]), cells=int(len(s)),
                         primes=int(pm.sum()), base=base,
                         reducible=is_square(B*B - 4*A*C)))
hl = hl_constants([r["A"] for r in rays], [r["B"] for r in rays], [r["C"] for r in rays])
for r, h in zip(rays, hl):
    r["hl"] = float(h); r["pred"] = 0.0 if r["reducible"] else float(h)*r["base"]

def summarize(group):
    g = [r for r in group if not r["reducible"]]
    obs = np.array([r["primes"] for r in g], float); pred = np.array([r["pred"] for r in g])
    live = pred > 0
    ratio = obs[live]/pred[live]
    return dict(rays=len(group), reducible=sum(r["reducible"] for r in group),
                dead_even=int(np.sum(~live)), dead_even_observed_primes=int(obs[~live].sum()),
                pearson_r=float(np.corrcoef(obs[live], pred[live])[0, 1]),
                obs_over_pred_median=float(np.median(ratio)),
                obs_over_pred_p05=float(np.percentile(ratio, 5)),
                obs_over_pred_p95=float(np.percentile(ratio, 95)),
                hl_min=float(np.min(np.array([r["hl"] for r in g])[live])),
                hl_max=float(np.max(np.array([r["hl"] for r in g])[live])))
diag = [r for r in rays if r["kind"] in KINDS_DIAG]
axis = [r for r in rays if r["kind"] in KINDS_AXIS]
R["rays"] = {"s_max": S_MAX, "offset_range": [-CR, CR], "all_rays_exactly_quadratic": True,
             "B_by_kind": {k: sorted({r["B"] for r in rays if r["kind"] == k}) for k in KINDS_DIAG + KINDS_AXIS},
             "diagonal": summarize(diag), "axis": summarize(axis)}
red = [r for r in rays if r["reducible"]]
R["rays"]["reducible_examples"] = [
    dict(kind=r["kind"], c=r["c"], f=f"{r['A']}s^2{r['B']:+d}s{r['C']:+d}", primes=r["primes"]) for r in red[:12]]
R["rays"]["reducible_total_primes"] = int(sum(r["primes"] for r in red))
live_diag = sorted([r for r in diag if r["pred"] > 0], key=lambda r: -r["hl"])
R["rays"]["richest_diagonals"] = [dict(kind=r["kind"], c=r["c"], f=f"4s^2{r['B']:+d}s{r['C']:+d}",
    hl=round(r["hl"], 3), primes=r["primes"], pred=round(r["pred"], 1), cells=r["cells"]) for r in live_diag[:6]]
R["rays"]["poorest_live_diagonals"] = [dict(kind=r["kind"], c=r["c"], f=f"4s^2{r['B']:+d}s{r['C']:+d}",
    hl=round(r["hl"], 3), primes=r["primes"], pred=round(r["pred"], 1), cells=r["cells"]) for r in live_diag[-4:]]
print("2. rays:", json.dumps(R["rays"]["diagonal"]), json.dumps(R["rays"]["axis"]))

# ---------------------------------------------------------------- 3. row streaks: cone vs wedge
rows = np.arange(1000, 1301)
seg_cone = np.arange(-900, 901)             # |x| < |y|: row runs along the top side of a shell
seg_wedge = np.arange(1400, 3201)           # |x| > |y|: row crosses shells, n quadratic in x
def row_counts(seg):
    X, Y = np.meshgrid(seg, rows)
    n = idx(X, Y); return isprime(n).sum(1), n
cc, ncone = row_counts(seg_cone); cw, nwedge = row_counts(seg_wedge)
def poisson_sd(n):
    # expected binomial sd if primes were independent with density 1/ln n
    p = 1/np.log(n.astype(float)); return np.sqrt((p*(1-p)).sum(1)).mean()
row_hl = hl_constants(np.full(len(rows), 4), np.full(len(rows), -3), 1 + rows)   # E wedge: 4s^2 - 3s + 1 + Y
R["row_streaks"] = {
    "rows": [int(rows[0]), int(rows[-1])], "cells_per_segment": int(len(seg_cone)),
    "cone": {"mean": float(cc.mean()), "sd": float(cc.std()), "sd_if_random": float(poisson_sd(ncone)),
             "sd_ratio": float(cc.std()/poisson_sd(ncone))},
    "wedge": {"mean": float(cw.mean()), "sd": float(cw.std()), "sd_if_random": float(poisson_sd(nwedge)),
              "sd_ratio": float(cw.std()/poisson_sd(nwedge)),
              "corr_with_hl_constant": float(np.corrcoef(cw, row_hl)[0, 1]),
              "min_count": int(cw.min()), "max_count": int(cw.max()),
              "hl_min": float(row_hl.min()), "hl_max": float(row_hl.max())}}
print("3. row streaks:", json.dumps(R["row_streaks"]))

# ---------------------------------------------------------------- 4. layer coincidence (renderer sampling)
P = 600
q = np.arange(-P, P+1)
QX, QY = np.meshgrid(q, q)
def layer(z):
    cx = np.floor(QX/z + 0.5).astype(np.int64); cy = np.floor(QY/z + 0.5).astype(np.int64)
    n = idx(cx, cy)
    return isprime(n), (n % 2 == 1) & (n >= 3), (np.gcd(n, 30) == 1)
pA, oA, wA = layer(1.0)
coinc = []
for name, r in [("1.25", 1.25), ("sqrt2", 2**0.5), ("1.5", 1.5), ("phi", (1+5**0.5)/2),
                ("2", 2.0), ("e", math.e), ("3", 3.0), ("4", 4.0)]:
    pB, oB, wB = layer(r)
    lift = (pA & pB).mean()/(pA.mean()*pB.mean())
    plift = (oA & oB).mean()/(oA.mean()*oB.mean())
    wlift = (wA & wB).mean()/(wA.mean()*wB.mean())
    coinc.append(dict(ratio=name, value=round(r, 4), P_A=round(float(pA.mean()), 4), P_B=round(float(pB.mean()), 4),
                      P_both=round(float((pA & pB).mean()), 5), lift=round(float(lift), 3),
                      parity_lift=round(float(plift), 3), coprime30_lift=round(float(wlift), 3),
                      residual_after_30=round(float(lift/wlift), 3),
                      xor_lit=round(float((pA ^ pB).mean()), 4)))
R["coincidence"] = {"pixels": f"{2*P+1}x{2*P+1}", "layer_A_cell_px": 1, "table": coinc}
print("4. coincidence:", json.dumps(coinc))

# ---------------------------------------------------------------- 5. paired polynomials on the main diagonals
def bh_pair(f, g, plist):
    logc = 0.0
    for p in plist:
        s = np.arange(p, dtype=object)
        w = sum(1 for t in range(p) if (f(t)*g(t)) % p == 0)
        logc += math.log(max(1 - w/p, 1e-300)) - 2*math.log(1 - 1/p)
    return math.exp(logc)
pairs = []
M = 1500
main = {"NE": (lambda s: 4*s*s - 2*s + 1), "NW": (lambda s: 4*s*s + 1), "SW": (lambda s: 4*s*s + 2*s + 1)}
for kind, f in main.items():
    # check against the page's indexing
    s = np.arange(1, 50); x, y = ray_points(kind, 0, s)
    assert np.array_equal(idx(x, y), np.array([f(int(t)) for t in s]))
    for rr in (2, 3):
        g = (lambda f, rr: (lambda s: f(rr*s)))(f, rr)
        m = np.arange(1, M+1, dtype=np.int64)
        fm = np.array([f(int(t)) for t in m]); gm = np.array([g(int(t)) for t in m])
        both = int((isprime(fm) & isprime(gm)).sum())
        C2 = bh_pair(f, g, [int(p) for p in SMALLP if p < 3000])
        pred = C2*float(np.sum(1/(np.log(fm.astype(float))*np.log(gm.astype(float)))))
        pairs.append(dict(ray=kind, f={"NE": "4s^2-2s+1", "NW": "4s^2+1", "SW": "4s^2+2s+1"}[kind],
                          ratio=rr, m_max=M, both_prime=both, bh_constant=round(C2, 3), predicted=round(pred, 1)))
R["paired_diagonals"] = pairs
print("5. pairs:", json.dumps(pairs))

# ---------------------------------------------------------------- 6. density shading calibration
def shade(z, P):
    """Exact emulation of the page's sub-pixel sampling for one layer, pixels in [-P, P]^2."""
    q = np.arange(-P, P+1)
    a = (q - 0.5)/z; b = (q + 0.5)/z
    c0 = np.floor(a - 0.5).astype(np.int64) + 1; c1 = np.ceil(b + 0.5).astype(np.int64) - 1
    lo, hi = c0.min(), c1.max()
    cs = np.arange(lo, hi+1); CX, CY = np.meshgrid(cs, cs)
    pg = isprime(idx(CX, CY)).astype(np.int64)
    I = np.zeros((len(cs)+1, len(cs)+1), np.int64); I[1:, 1:] = pg.cumsum(0).cumsum(1)
    X0, Y0 = np.meshgrid(c0 - lo, c0 - lo); X1, Y1 = np.meshgrid(c1 - lo + 1, c1 - lo + 1)
    cnt = I[Y1, X1] - I[Y0, X1] - I[Y1, X0] + I[Y0, X0]
    area = (X1 - X0)*(Y1 - Y0)
    nlast = idx(*np.meshgrid(c1, c1))
    v = np.minimum(1.0, cnt/area*np.log(np.maximum(nlast, 3))*0.5)
    QX, QY = np.meshgrid(q, q); rad = np.maximum(np.abs(QX), np.abs(QY))
    return v, rad, int(c1[0] - c0[0] + 1)
shading = []
for z, Pz in [(0.5, 400), (0.25, 400), (0.1, 300)]:
    v, rad, per_axis = shade(z, Pz)
    bins = np.linspace(20, Pz, 6).astype(int)
    rows_ = []
    for lo_, hi_ in zip(bins[:-1], bins[1:]):
        m = (rad >= lo_) & (rad < hi_)
        nmid = int((2*((lo_+hi_)/2)/z)**2)
        rows_.append(dict(radius_px=f"{lo_}-{hi_}", n_around=nmid, mean_v=round(float(v[m].mean()), 3),
                          clipped=round(float((v[m] >= 1).mean()), 3)))
    shading.append(dict(z=z, cells_per_px_area=round(1/z**2, 1), cells_sampled_per_axis=per_axis, bins=rows_))
R["shading"] = shading
print("6. shading:", json.dumps(shading))

# ---------------------------------------------------------------- 7. Euler line at centre number 41
def line_run(start, kind, c, T=60):
    t = np.arange(-T, T+1)
    x, y = (t + c, t) if kind == "x-y" else (c - t, t)
    n = idx(x, y) + start - 1
    pm = isprime(n); best = cur = 0
    for v in pm:
        cur = cur + 1 if v else 0; best = max(best, cur)
    return best, float(pm.mean())
eul = []
for kind in ("x-y", "x+y"):
    for c in range(-20, 21):
        run, frac = line_run(41, kind, c)
        eul.append(dict(line=f"{kind}={c}", longest_prime_run=run, prime_fraction_within_60=round(frac, 3)))
eul.sort(key=lambda d: -d["longest_prime_run"])
R["euler41"] = eul[:4]
print("7. euler41:", json.dumps(eul[:4]))

# ---------------------------------------------------------------- figures
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(figsize=(6.4, 5.2))
for grp, col, lab in [(diag, "#cf2878", "diagonal rays"), (axis, "#0096c4", "row / column rays")]:
    g = [r for r in grp if not r["reducible"] and r["pred"] > 0]
    ax.scatter([r["pred"] for r in g], [r["primes"] for r in g], s=5, alpha=0.5, color=col, label=lab)
mx = max(r["pred"] for r in rays)
ax.plot([0, mx], [0, mx], color="#1a1f1d", lw=0.8)
ax.set_xlabel("Hardy-Littlewood prediction (primes on ray)")
ax.set_ylabel("primes counted on ray")
ax.set_title(f"Every straight ray of the spiral, s up to {S_MAX}")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "rays_vs_hardy_littlewood.png"), dpi=140)

fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.plot(rows, cw, color="#cf2878", lw=0.9, label="outside the cone (|x| > |y|)")
ax.plot(rows, cc, color="#0096c4", lw=0.9, label="inside the cone (|x| < |y|)")
ax.set_xlabel("row y"); ax.set_ylabel(f"primes in {len(seg_cone)} cells")
ax.set_title("Why rows streak: same-length segments of each row")
ax.legend(frameon=False, loc="upper right")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "row_streaks.png"), dpi=140)


# ---------------------------------------------------------------- 8. ratio sweep
P8 = 500
q8 = np.arange(-P8, P8+1); X8, Y8 = np.meshgrid(q8, q8)
def cells_n(z):
    return idx(np.floor(X8/z + 0.5).astype(np.int64), np.floor(Y8/z + 0.5).astype(np.int64))
nA8 = cells_n(1.0); pA8 = isprime(nA8)
def lift(a, b): return float((a & b).mean()/(a.mean()*b.mean()))
sweep_r = np.round(np.arange(1.01, 4.0001, 0.01), 3)
sweep = []
for r in sweep_r:
    pB8 = isprime(cells_n(float(r)))
    sweep.append(lift(pA8, pB8))
sweep = np.array(sweep)
from fractions import Fraction
def near_simple(r, qmax=12, tol=0.006):
    f = Fraction(float(r)).limit_denominator(qmax)
    return abs(float(f) - r) < tol and f.denominator <= qmax
far = np.array([not near_simple(r, 6) for r in sweep_r])
exact = []
for name, r in [("3/2", 3/2), ("5/3", 5/3), ("2", 2.0), ("5/2", 5/2), ("7/3", 7/3), ("3", 3.0),
                ("13/4", 13/4), ("7/2", 7/2), ("11/3", 11/3), ("11/5", 11/5)]:
    nB8 = cells_n(r)
    row = dict(ratio=name, lift=round(lift(pA8, isprime(nB8)), 3))
    for M, lab in [(2, "up_to_2"), (6, "up_to_3"), (30, "up_to_5"), (210, "up_to_7"), (2310, "up_to_11")]:
        row[lab] = round(lift(np.gcd(nA8, M) == 1, np.gcd(nB8, M) == 1), 3)
    exact.append(row)
R["ratio_sweep"] = {"pixels": f"{2*P8+1}x{2*P8+1}", "step": 0.01,
                    "lift_away_from_fractions_q_le_6": {"mean": round(float(sweep[far].mean()), 3),
                                                       "sd": round(float(sweep[far].std()), 3)},
                    "largest_deviations": [dict(r=float(sweep_r[i]), lift=round(float(sweep[i]), 3))
                                           for i in np.argsort(-np.abs(sweep - 1))[:8]],
                    "exact_fractions": exact}
print("8. sweep:", json.dumps(R["ratio_sweep"]))

# ---------------------------------------------------------------- 9. Checker, 1 px band: dead slots
# slot = (dx + dy) mod L; a layer at z = 1 reads cell (dx, -dy), whose x + y has the parity of dx + dy.
L9 = 6
dead = {}
for slot in range(L9):
    m = (np.mod(X8 + Y8, L9) == slot)
    nn = idx(X8[m], -Y8[m])
    dead[slot] = dict(odd_numbers=int((nn % 2 == 1).sum()), primes=int(isprime(nn).sum()))
R["checker_1px"] = {"layers": L9, "layer_cell_px": 1, "by_slot": dead}
print("9. checker:", json.dumps(dead))

# ---------------------------------------------------------------- sweep figure
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.axhline(1, color="#58635e", lw=0.6)
ax.plot(sweep_r, sweep, color="#1f3fae", lw=0.9)
for name, r in [("3/2", 1.5), ("5/3", 5/3), ("2", 2), ("5/2", 2.5), ("3", 3), ("7/2", 3.5), ("11/3", 11/3)]:
    i = int(np.argmin(np.abs(sweep_r - r))); ax.annotate(name, (sweep_r[i], sweep[i]), textcoords="offset points", xytext=(0, 6 if sweep[i] > 1 else -12), ha="center", fontsize=8)
ax.set_xlabel("ratio r between layer B and layer A (A at 1 px per cell)")
ax.set_ylabel("coincidence lift")
ax.set_title("Shared primes between two layers, relative to independence")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "ratio_sweep.png"), dpi=140)

R["runtime_s"] = round(time.time() - t_start, 1)
with open(os.path.join(HERE, "results.json"), "w") as fh:
    json.dump(R, fh, indent=2)
print("done in", R["runtime_s"], "s")
