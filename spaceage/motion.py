"""Real motion for a still picture: a slow 2.5D camera move with depth parallax plus drifting particles.

Instagram does not monetize "static videos" (a still image with little or no movement), so a reel
is no longer just a slow zoom. frames(img, ...) yields the reel's frames one by one (numpy only,
no extra packages, little memory):

- depth: a rough depth map from the picture's layout. Claude names the horizon and the box of the
  main subject (mood.layout_of); below the horizon the ground comes nearer towards the bottom, the
  sky stays far, and the subject stands at the depth of the ground at its feet. Without Claude the
  bottom of the picture counts as near and the top as far.
- camera: one of three moves per picture (push in, drift sideways, rise), eased in and out. With
  parallax=True near parts move more than far parts; that is off by default, because a depth map
  guessed from the layout morphs rigid objects.
- particles: dust, embers, ash or sparks that suit the mood, in three depths, plus a faint
  breathing of the light.
"""

import math

import numpy as np

BASE = 1.07  # overscan, so the moving picture never shows its edges


def _blur(a, r):
    """Separable box blur, twice (close to a gaussian), on a 2D float array."""
    for _ in range(2):
        for axis in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def depth_map(w, h, horizon=None, box=None):
    """0 = far, 1 = near."""
    y = (np.arange(h, dtype=np.float32) + 0.5) / h
    if horizon is None:
        col = 0.12 + 0.75 * y ** 1.3
    else:
        col = np.where(y < horizon, 0.05 + 0.08 * y / horizon,
                       0.15 + 0.85 * np.clip((y - horizon) / (1 - horizon), 0, 1) ** 0.9)
    d = np.repeat(col[:, None], w, axis=1).astype(np.float32)
    if box:
        x0, y0, x1, y1 = box
        foot = 0.6 if horizon is None or y1 <= horizon else float(np.interp(y1, y, col))
        foot = max(0.5, min(0.95, foot))
        fx, fy = max(0.02, (x1 - x0) * 0.12), max(0.02, (y1 - y0) * 0.12)
        xs = (np.arange(w, dtype=np.float32) + 0.5) / w
        mx = np.clip(np.minimum(xs - x0, x1 - xs) / fx + 0.5, 0, 1)
        my = np.clip(np.minimum(y - y0, y1 - y) / fy + 0.5, 0, 1)
        m = my[:, None] * mx[None, :]
        d = d * (1 - m) + np.maximum(d, foot) * m
    return _blur(d, max(4, w // 40))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


PARTICLES = {  # kind: (count, colour, speed (x, y) in frame heights per second, size px, twinkle)
    "dust": (140, (255, 238, 205), (0.006, -0.004), 2.8, 0.6),
    "embers": (110, (255, 160, 70), (0.004, -0.030), 3.0, 0.8),
    "ash": (150, (230, 230, 235), (0.006, 0.022), 3.0, 0.3),
    "sparks": (90, (170, 225, 255), (0.010, -0.006), 2.4, 0.9),
}
MOOD_PARTICLES = {"action": "embers", "industry": "embers", "sorrow": "ash", "eerie": "ash",
                  "neon": "sparks", "cosmic": "sparks", "deep": "dust"}


def _sprite(r):
    k = int(math.ceil(r * 2.5))
    g = np.arange(-k, k + 1, dtype=np.float32)
    return np.exp(-(g[:, None] ** 2 + g[None, :] ** 2) / (2 * (r / 1.6) ** 2))


def frames(img, seconds, fps, seed, mood=None, horizon=None, box=None, parallax=False):
    """img: PIL RGB image already in reel size. Yields uint8 HxWx3 frames."""
    rng = np.random.default_rng(seed)
    src = np.asarray(img, dtype=np.uint8)
    h, w = src.shape[:2]
    flat = src.reshape(-1, 3)
    # The camera moves the picture as one rigid plane. A depth map from the layout alone bent rigid
    # things (a saucer, a face) like rubber, so parallax stays off until a real depth model is used.
    depth = np.full((h, w), 0.6, dtype=np.float32) if not parallax else depth_map(w, h, horizon, box)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    dxrow = np.arange(w, dtype=np.float32) - cx
    STRIP = 160  # rows warped at once: keeps the memory small (the server has 1 GB)
    move = ["push", "drift", "rise"][int(rng.integers(3))]
    side = 1 if rng.random() < 0.5 else -1
    amp = w * 0.022  # largest shift of the nearest parts, in pixels

    kind = MOOD_PARTICLES.get(mood, "dust")
    count, colour, speed, size, twinkle = PARTICLES[kind]
    layer = rng.choice([0.3, 0.6, 1.0], count, p=[0.5, 0.3, 0.2])  # depth of each particle
    px = rng.random(count) * w
    py = rng.random(count) * h
    vx = (speed[0] * (rng.random(count) - 0.5) * 2 + speed[0] * 0.3) * h * layer
    vy = speed[1] * h * layer * (0.6 + 0.8 * rng.random(count))
    phase = rng.random(count) * 2 * math.pi
    sprites = {s: _sprite(s) for s in (size * 0.6, size, size * 1.6)}
    sizes = np.where(layer < 0.5, size * 0.6, np.where(layer < 0.9, size, size * 1.6))
    col = np.array(colour, dtype=np.float32)

    n = int(round(seconds * fps))
    out = np.empty((h, w, 3), dtype=np.float32)
    for i in range(n):
        t = i / max(1, n - 1)
        e = _ease(t)
        for r0 in range(0, h, STRIP):
            d = depth[r0:r0 + STRIP]
            dy = (np.arange(r0, r0 + d.shape[0], dtype=np.float32) - cy)[:, None]
            if move == "push":
                z = BASE * (1 + e * (0.02 + 0.08 * d))
                sx = sy = 0.0
            elif move == "drift":
                z = BASE * (1 + e * (0.01 + 0.03 * d))
                sx, sy = side * (e - 0.5) * 2 * amp * (0.15 + d), 0.0
            else:
                z = BASE * (1 + e * (0.01 + 0.03 * d))
                sx, sy = 0.0, -(e - 0.5) * 2 * amp * 0.8 * (0.15 + d)
            qx = np.clip(cx + dxrow[None, :] / z - sx, 0, w - 1.001)
            qy = np.clip(cy + dy / z - sy, 0, h - 1.001)
            x0 = qx.astype(np.int32)
            y0 = qy.astype(np.int32)
            fx = (qx - x0)[..., None]
            fy = (qy - y0)[..., None]
            i00 = y0 * w + x0
            top = flat[i00] * (1 - fx) + flat[i00 + 1] * fx
            bottom = flat[i00 + w] * (1 - fx) + flat[i00 + w + 1] * fx
            out[r0:r0 + d.shape[0]] = top * (1 - fy) + bottom * fy
        out *= 1 + 0.015 * math.sin(2 * math.pi * t * 0.7 + phase[0])  # the light breathes a little

        # particles: move, wrap around, draw as soft dots with a gentle twinkle
        tx = (px + vx * i / fps - side * e * amp * layer * (move == "drift")) % w
        ty = (py + vy * i / fps) % h
        alpha = 0.8 * layer * (1 - twinkle * 0.5 * (1 + np.sin(phase + i / fps * 2.5)))
        alpha *= min(1.0, i / (0.6 * fps), (n - 1 - i) / (0.6 * fps) + 0.2)  # fade in and out
        for j in range(count):
            spr = sprites[sizes[j]]
            k = spr.shape[0] // 2
            ix, iy = int(tx[j]), int(ty[j])
            xa, xb, ya, yb = max(0, ix - k), min(w, ix + k + 1), max(0, iy - k), min(h, iy + k + 1)
            if xa >= xb or ya >= yb:
                continue
            s = spr[ya - iy + k:yb - iy + k, xa - ix + k:xb - ix + k, None] * alpha[j]
            region = out[ya:yb, xa:xb]
            region += (col - region) * s
        yield np.clip(out, 0, 255).astype(np.uint8)
