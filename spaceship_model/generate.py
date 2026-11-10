#!/usr/bin/env python3
"""Parametric generator for an original long-spine deep-space ship model.

Produces print-ready STL parts (each already in print orientation, flat on
the bed, no supports needed) plus an assembled preview mesh.

Usage:  python3 generate.py            (needs: pip install manifold3d numpy)
All dimensions in millimetres. Tuned for a 0.2 mm nozzle.
"""
import math
import os
import random
from collections import defaultdict
import struct

import numpy as np
from manifold3d import CrossSection, Manifold, OpType

# ----------------------------------------------------------------- parameters
CLEAR = 0.15          # radial clearance for plug/socket fits
LED_D = 3.2           # hole for a 3 mm LED
ROD_D = 8.0           # wooden core rod (beech dowel) through neck, spine and adapter
WIRE_R = 1.6          # wire channel running along the top of the rod
WIRE_OFF = 4.65       # its centre distance from the axis
PLUG_D = 12.0         # spine connector plug diameter
PLUG_L = 8.0

CREW_R = 36.0         # design radius of the crew sphere; all sphere detail is modelled at this size
CREW_SCALE = 1.125    # the finished sphere, cockpit and joiner ring are scaled by this factor (81 mm sphere)
CREW_RS = CREW_R * CREW_SCALE
CREW_CYL = 0.0        # optional cylindrical stretch per half; 0 = pure sphere
CREW_WALL = 1.6
NECK_R = 10.0
NECK_L = 16.0

SPINE_R = 10.0        # circumradius of octagonal spine core
SEG_L = 126.0         # length of one spine segment
N_SEG = 4             # number of spine segments (sphere diameter : length = 1 : 10)

BLOCK_R = 25.0        # circumradius of octagonal reactor block
BLOCK_L = 124.0       # battery tray (84) + switch bay + joints
BLOCK_CAV_R = 23.0
ENG_OFF = 11.5        # vertical nozzle offset (two rows)
ENG_COL = 23.0        # horizontal spacing of the three nozzle columns
ENG_R = 10.0
ENG_L = 30.0
NOZ_L = 16.0          # length of the bell nozzle
NOZ_RT = 1.6          # throat radius = 3 mm LED, which sits in the throat
NOZ_LED_OUT = 1.5     # how far the LED tip protrudes into the bell
NOZ_WIRE_R = 2.2      # passage for the LED legs and wires behind the nozzle
NOZ_WALL = 0.8
NOZ_FLANGE = 3.5      # flange height between bell and plug
NOZ_PLUG_R = 3.4
NOZ_PLUG_L = 5.0

SWITCH_CUT = (9.0, 13.5)   # panel cutout of a mini rocker switch (KCD11 type): across x along the ship
TRAY_L = 84.0              # length of the removable battery tray (holder up to 79 mm)
TRAY_CUT = -12.0           # the tray is everything below this height (print x of the block)
PIN_D = 1.75               # locking pin of the tray = a piece of filament
LUG_HOLE = 3.2             # eye diameter of the suspension lugs
SEED = 2001

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
rng = random.Random(SEED)


# -------------------------------------------------------------------- helpers
def cyl(h, r, r2=None, seg=96, z=0.0):
    return Manifold.cylinder(h, r, r if r2 is None else r2, seg).translate([0, 0, z])


def octa(h, r, z=0.0):
    """Octagonal prism with flats facing +-x / +-y. r = circumradius."""
    return Manifold.cylinder(h, r, r, 8).rotate([0, 0, 22.5]).translate([0, 0, z])


def box(sx, sy, sz, cx=0.0, cy=0.0, cz=0.0):
    return Manifold.cube([sx, sy, sz], True).translate([cx, cy, cz])


def union(parts):
    return Manifold.batch_boolean(list(parts), OpType.Add)


def hull(*parts):
    return Manifold.batch_hull(list(parts))


def rz(m, deg):
    return m.rotate([0, 0, deg])


def clean(m):
    """Remove specks (< 0.5 mm^3) that boolean operations on touching surfaces can leave behind."""
    comps = m.decompose()
    if len(comps) <= 1:
        return m
    return Manifold.compose([c for c in comps if c.volume() > 0.5])


def write_stl(m, name):
    m = clean(m)
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float32)[:, :3]
    t = np.asarray(mesh.tri_verts, dtype=np.uint32)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(b"original spine ship model".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(rec.tobytes())
    lo, hi = v.min(0), v.max(0)
    print(f"{name:28s} tris={len(t):6d} size={hi[0]-lo[0]:6.1f} x {hi[1]-lo[1]:6.1f} x {hi[2]-lo[2]:6.1f}"
          f"  zmin={lo[2]:.2f} genus={m.genus()} status={m.status()}")
    return path


def face_greebles(apothem, half_w, z0, z1, n_per_face, faces=8, skip=None,
                  w_rng=(2.0, 9.0), l_rng=(2.5, 14.0), heights=(0.4, 0.6, 0.8)):
    """Random raised panels on the flats of a prism (print axis = z)."""
    out = []
    step = 360.0 / faces
    for k in range(faces):
        for _ in range(n_per_face):
            w = rng.uniform(w_rng[0], min(w_rng[1], 2 * half_w - 1))
            l = rng.uniform(*l_rng)
            h = rng.choice(heights)
            t = rng.uniform(-(half_w - w / 2 - 0.4), half_w - w / 2 - 0.4)
            z = rng.uniform(z0 + l / 2, z1 - l / 2)
            if skip and skip(k, t, z, w, l):
                continue
            out.append(rz(box(2 * h, w, l, apothem, t, z), k * step))
    return out


def wedge(a0, a1, z0, z1, reach=200.0):
    """Pie-slice prism around the z axis between two azimuths (deg, span < 180)."""
    pts = []
    for z in (z0, z1):
        pts.append((0.0, 0.0, z))
        n = max(2, int((a1 - a0) / 20) + 2)
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * i / (n - 1))
            pts.append((reach * math.cos(a), reach * math.sin(a), z))
    return Manifold.hull_points(pts)


# ------------------------------------------------------------------ detail kit
# Every kit element lives in a local frame: x = outward from the surface (x = 0),
# y = across the face, z = along the print axis (0 .. l). Protrusions stay small
# or get a 45 deg fairing so that everything prints without supports.
def xcyl(h, r, x0=0.0, seg=24):
    return Manifold.cylinder(h, r, r, seg).rotate([0, 90, 0]).translate([x0, 0, 0])


def kit_zone(kind, w, l):
    adds, local_cuts, body_cuts = [], [], []
    zc = l / 2
    if kind == "pipes":                                    # pipe bundle with clamps and a valve
        r = rng.uniform(0.5, 0.75)
        pitch = 2 * r + 0.45
        n = max(1, min(rng.randint(2, 4), int((w - 0.4) / pitch)))
        ys = [(i - (n - 1) / 2) * pitch for i in range(n)]
        for y in ys:
            adds.append(cyl(l - 0.6, r, seg=12, z=0.3).translate([r * 0.5, y, 0]))
        z = rng.uniform(1.5, 3.0)
        while z < l - 1.5:
            adds.append(box(r * 1.5 + 0.5, n * pitch + 0.3, 0.8, (r * 1.5 + 0.5) / 2 - 0.3, 0, z))
            z += rng.uniform(5.0, 8.0)
        if l > 8:
            adds.append(box(2 * r + 0.9, 2 * r + 0.5, 1.8, r * 0.5, rng.choice(ys), rng.uniform(3, l - 3)))
    elif kind == "hpipes":                                 # cross pipes between two manifolds
        m = max(1, min(4, int(l / 2.6)))
        for i in range(m):
            adds.append(cyl(w - 1.6, 0.6, seg=12).rotate([90, 0, 0]).translate([0.3, (w - 1.6) / 2, l * (i + 0.5) / m]))
        for sy in (-1, 1):
            adds.append(box(1.5, 1.3, l - 0.6, 0.45, sy * (w / 2 - 0.65), zc))
    elif kind == "hatch_round":                            # round airlock with bolts, handle, hinge
        R = min(min(w, l) / 2 - 0.3, 6.0)
        adds.append(xcyl(1.2, R, -0.3, 48) - xcyl(1.0, R - 1.1, 0.45, 48))
        for k in range(8):
            a = math.radians(45 * k + 22.5)
            adds.append(xcyl(1.45, 0.32, -0.3, 12).translate([0, (R - 0.55) * math.cos(a), (R - 0.55) * math.sin(a)]))
        adds.append(box(0.5, (R - 1.1) * 1.3, 0.6, 0.6, 0, 0))
        adds.append(box(1.3, 1.3, 2.6, 0.35, -(R - 0.4), 0))
        adds = [union(adds).translate([0, 0, zc])]
    elif kind == "hatch_rect":                             # rectangular door with window and handle
        W, L = min(w - 0.4, 7.5), min(l - 0.4, 11.5)
        adds.append(box(1.2, W, L, 0.3, 0, zc) - box(1.0, W - 1.6, L - 1.6, 0.95, 0, zc))
        local_cuts.append(box(0.6, (W - 1.6) * 0.55, 1.3, 0.45, 0, zc + L * 0.22))
        adds.append(box(0.6, 0.5, 2.0, 0.65, (W - 1.6) / 2 - 0.8, zc - 0.6))
    elif kind == "vent":                                   # louvred vent
        W, L = w - 0.4, min(l - 0.4, 9.0)
        adds.append(box(1.0, W, L, 0.2, 0, zc) - box(1.0, W - 1.2, L - 1.2, 0.75, 0, zc))
        z = zc - L / 2 + 1.1
        while z < zc + L / 2 - 0.9:
            adds.append(box(0.9, W - 1.0, 0.45, 0.2, 0, z))
            z += 1.0
    elif kind == "panel":                                  # riveted plate with equipment boxes
        adds.append(box(0.8, w - 0.4, l - 0.4, 0, 0, zc))
        if w >= 3.5 and l >= 3.5:
            for sy in (-1, 1):
                for sz in (-1, 1):
                    adds.append(xcyl(1.0, 0.35, -0.3, 12).translate([0, sy * (w / 2 - 1.0), zc + sz * (l / 2 - 1.0)]))
        for _ in range(rng.randint(1, 3)):
            bw = rng.uniform(1.2, max(1.3, w * 0.5))
            bl = rng.uniform(1.2, max(1.3, l * 0.45))
            adds.append(box(2 * rng.choice([0.8, 1.0, 1.2]), bw, bl, 0,
                            rng.uniform(-(w - bw) / 2 + 0.3, (w - bw) / 2 - 0.3) if w - bw > 0.7 else 0,
                            zc + (rng.uniform(-(l - bl) / 2 + 0.3, (l - bl) / 2 - 0.3) if l - bl > 0.7 else 0)))
    elif kind == "tanks":                                  # pressure tanks with straps and fairing
        n = max(1, min(3, int(w / 4.4)))
        r = min(2.0, (w / n - 0.5) / 2)
        zb, zt = 1.75 * r + 0.6, l - r * 0.8 - 0.4
        for i in range(n):
            y = (i - (n - 1) / 2) * (2 * r + 0.5)
            adds.append(cyl(zt - zb, r, seg=24, z=zb).translate([0.75 * r, y, 0]))
            adds.append(hull(cyl(0.05, r, seg=24, z=zb).translate([0.75 * r, y, 0]), box(0.02, 1.4, 0.02, -0.2, y, 0.3)))
            adds.append(cyl(r * 0.8, r, r * 0.4, seg=24, z=zt - 0.01).translate([0.75 * r, y, 0]))
            for f in (0.25, 0.75):
                adds.append(cyl(0.7, r + 0.3, seg=24, z=zb + (zt - zb) * f).translate([0.75 * r, y, 0]))
    elif kind == "trench":                                 # recessed channel with a pipe inside
        body_cuts.append(box(1.6, 2.2, l - 0.6, 0.2, 0, zc))
        for sy in (-1, 1):
            adds.append(box(0.75, 0.5, l - 0.6, 0.075, sy * 1.35, zc))
        adds.append(cyl(l - 1.4, 0.55, seg=12, z=0.7).translate([-0.1, 0, 0]))
        z = rng.uniform(1.5, 3.0)
        while z < l - 1.5:
            adds.append(box(0.9, 3.2, 0.7, 0.15, 0, z))
            z += rng.uniform(4.5, 7.0)
    solid = union(adds)
    if local_cuts:
        solid -= union(local_cuts)
    return solid, (union(body_cuts) if body_cuts else None)


KIT_RULES = [  # kind, weight, min w, max w, min l
    ("pipes", 3.0, 2.2, 99, 6), ("hpipes", 1.5, 6, 99, 5), ("hatch_round", 1.6, 8, 99, 8),
    ("hatch_rect", 1.6, 6, 99, 9), ("vent", 2.0, 4, 99, 4), ("panel", 2.6, 2.2, 99, 3),
    ("tanks", 1.6, 5, 99, 10), ("trench", 1.6, 3.5, 9, 7)]


def face_layout(W, z0, z1):
    """Split a face into zones and pick a fitting kit element for each."""
    out, hatches, z = [], 0, z0
    while z < z1 - 3:
        l = rng.uniform(7.0, 15.0)
        if z1 - (z + l) < 5:
            l = z1 - z
        cols = [(0.0, W)]
        if W >= 13 and rng.random() < 0.7:
            f = rng.uniform(0.35, 0.65)
            cols = [(-W / 2 + W * f / 2, W * f), (W / 2 - W * (1 - f) / 2, W * (1 - f))]
        for t, w in cols:
            ww, ll = w - 0.5, l - 0.5
            cand = [(k, wt) for k, wt, wmin, wmax, lmin in KIT_RULES
                    if wmin <= ww <= wmax and ll >= lmin and not (k.startswith("hatch") and hatches >= 2)]
            kind = rng.choices([c[0] for c in cand], [c[1] for c in cand])[0]
            hatches += kind.startswith("hatch")
            out.append((kind, t, z + 0.25, ww, ll))
        z += l
    return out


def detail_face(apothem, W, z0, z1, angle, t0=0.0, blank=None):
    adds, cuts = [], []
    for kind, t, z, w, l in face_layout(W, z0, z1):
        if blank and blank(t, z, w, l):
            continue
        solid, c = kit_zone(kind, w, l)
        adds.append(rz(solid.translate([apothem, t0 + t, z]), angle))
        if c is not None:
            cuts.append(rz(c.translate([apothem, t0 + t, z]), angle))
    return adds, cuts


def core_bore(h, z=0.0):
    """Bore for the wooden rod with a wire channel on its upper side (+x)."""
    return cyl(h, ROD_D / 2 + 0.2, seg=48, z=z) + cyl(h, WIRE_R, seg=24, z=z).translate([WIRE_OFF, 0, 0])


def plug_key(z0, length=None):
    """Rib on a round plug (at +x) so that the joint only fits in one orientation."""
    length = PLUG_L if length is None else length
    return box(1.6, 3.4, length, PLUG_D / 2 + 0.2, 0, z0 + length / 2)


def socket_key(z0, depth):
    """Matching keyway for plug_key (at +x), with clearance."""
    return box(1.9, 3.8, depth, PLUG_D / 2 + 0.3, 0, z0 + depth / 2)


def lug(apothem, z0, length=10.0, reach=8.0, thick=4.0):
    """Suspension eye on the +x flat of a part printed along z. The pull acts within the layers
    and the underside slopes, so it prints without support."""
    zc = z0 + length - 4.0
    eye = cyl(thick, 4.0, seg=48, z=-thick / 2).rotate([90, 0, 0]).translate([apothem + reach - 4.0, 0, zc])
    root = box(0.02, thick, length + reach, apothem - 0.6, 0, z0 + (length - reach) / 2)
    hole = cyl(thick + 2, LUG_HOLE / 2, seg=32, z=-thick / 2 - 1).rotate([90, 0, 0]).translate([apothem + reach - 4.0, 0, zc])
    return hull(eye, root), hole


# ----------------------------------------------------------------- crew module
def crew_shell(solid_extra=0.0):
    r = CREW_R + solid_extra
    parts = [Manifold.sphere(r, 128).translate([0, 0, CREW_CYL])]
    if CREW_CYL > 0:
        parts.append(cyl(CREW_CYL, r))
    return union(parts).trim_by_plane([0, 0, 1], 0)


def crew_inner():
    r = CREW_R - CREW_WALL
    parts = [Manifold.sphere(r, 128).translate([0, 0, CREW_CYL])]
    if CREW_CYL > 0:
        parts.append(cyl(CREW_CYL + 0.2, r, z=-0.1))
    return union(parts)


_LIFT = {}


def lifted(l):
    if l not in _LIFT:
        _LIFT[l] = crew_shell(l)
    return _LIFT[l]


def crew_band(z, h=1.4, lift=0.5):
    """Raised belt following the hull between heights z and z+h."""
    return lifted(lift).trim_by_plane([0, 0, 1], z).trim_by_plane([0, 0, -1], -(z + h))


def zslab(z0, z1):
    return box(400, 400, z1 - z0, 0, 0, (z0 + z1) / 2)


def sph_dir(m, theta, phi):
    """Move geometry built around +z so that it points along polar angle theta / azimuth phi."""
    return rz(m.rotate([0, theta, 0]), phi).translate([0, 0, CREW_CYL])


def crew_plating(feat, z_edges):
    """Tiled hull plates of varying height, separated by fine panel gaps."""
    for za, zb in zip(z_edges[:-1], z_edges[1:]):
        r_here = math.sqrt(max(CREW_R ** 2 - (0.5 * (za + zb) - CREW_CYL) ** 2, 9.0))
        gap = math.degrees(0.45 / r_here)
        a = rng.uniform(0, 30)
        end = a + 360
        while a < end - 1:
            span = min(rng.uniform(5.0, 24.0) * (CREW_R / r_here) ** 0.5, end - a)
            lift = rng.choice([0, 0.3, 0.3, 0.3, 0.5, 0.5, 0.8])
            if lift and span > 2 * gap + 1:
                feat[lift].append(wedge(a + gap, a + span - gap, za + 0.22, zb - 0.22))
                if rng.random() < 0.4 and span > 5:       # small box on top of the plate
                    c = a + span * rng.uniform(0.25, 0.75)
                    w = min(span * 0.3, 5)
                    feat[round(lift + 0.5, 2)].append(wedge(c - w / 2, c + w / 2, za + 0.6, zb - 0.6))
            a += span


def crew_conduits(feat, z_max, n_lat, n_mer):
    """Pipes following the sphere: along latitudes and along meridians, with junction boxes."""
    for _ in range(n_lat):
        z = rng.uniform(3.0, z_max)
        a = rng.uniform(0, 360)
        feat[0.85].append(wedge(a, a + rng.uniform(40, 110), z, z + 0.7))
    for _ in range(n_mer):
        a = rng.uniform(0, 360)
        z0 = rng.uniform(2.5, z_max * 0.5)
        z1 = rng.uniform(z0 + 6, z_max)
        feat[0.85].append(rz(box(CREW_R + 6, 0.9, z1 - z0, (CREW_R + 6) / 2, 0, (z0 + z1) / 2), a))
        feat[1.2].append(rz(box(CREW_R + 6, 2.0, 1.7, (CREW_R + 6) / 2, 0, z0), a))
        feat[1.2].append(rz(box(CREW_R + 6, 1.6, 1.3, (CREW_R + 6) / 2, 0, z1), a))


def sph_hatch(feat2, clear, R, theta, phi):
    """Round airlock on the sphere: frame, recessed door, handle and bolts."""
    def C(r, seg=48):
        return sph_dir(cyl(CREW_R + 6, r, seg=seg), theta, phi)
    feat2[1.0].append(C(R) - C(R - 1.1))
    feat2[0.45].append(C(R - 1.1))
    feat2[0.9].append(sph_dir(box(0.7, 2 * (R - 1.7), CREW_R + 6, 0, 0, (CREW_R + 6) / 2), theta, phi))
    for k in range(10):
        a = math.radians(36 * k)
        b = cyl(CREW_R + 6, 0.4, seg=12).translate([(R - 0.55) * math.cos(a), (R - 0.55) * math.sin(a), 0])
        feat2[1.3].append(sph_dir(b, theta, phi))
    clear.append(C(R + 0.5))


def crew_build(feat, clear, feat2, grooves):
    def layer(d):
        return [lifted(l) ^ union(cs) for l, cs in d.items() if cs]
    body = union([crew_shell()] + layer(feat))
    if clear:
        body -= (lifted(3.0) - crew_shell()) ^ union(clear)
    body = union([body] + layer(feat2))
    if grooves:
        body -= (lifted(3.0) - crew_shell(-0.45)) ^ union(grooves)
    return body


FRONT_BANDS = [2.0, 4.8, 7.6, 10.4, 13.2, 16.0, 18.8, 21.4, 24.0, 26.4, 28.6, 30.6, 32.4, 34.0]
REAR_BANDS = [2.0, 4.8, 7.6, 10.4, 13.2, 16.0, 18.8, 21.4, 24.0, 26.4, 28.6, 30.6]


def crew_front():
    return _crew_front().scale([CREW_SCALE] * 3)


def _crew_front():
    """Front hemisphere. Print coords: +z = ship forward, +x = ship up."""
    zc = CREW_CYL
    feat, feat2, clear = defaultdict(list), defaultdict(list), []
    feat[0.6].append(zslab(0, 2.0))
    crew_plating(feat, FRONT_BANDS)
    crew_conduits(feat, 26.0, 7, 9)

    def slab(x0, x1, hy):
        return box(x1 - x0, 2 * hy, CREW_R, (x0 + x1) / 2, 0, zc + 10 + CREW_R / 2)

    cockpit = slab(1.6, 14.1, 25.0)
    clear.append(cockpit)
    feat2[0.9].append(slab(3.4, 12.1, 23.0))               # cockpit frame
    feat2[1.7].append(slab(12.1, 13.9, 24.5))              # brow above the windows
    feat2[1.3].append(slab(1.8, 3.4, 20.0))                # sill below the windows
    clear.append(wedge(166.5, 193.5, zc + 12, zc + 25))    # ventral hatch
    feat2[0.9].append(wedge(168, 192, zc + 13, zc + 24))
    feat2[0.45].append(wedge(166.9, 193.1, zc + 12.2, zc + 24.8))
    feat2[1.3].append(wedge(172, 188, zc + 15, zc + 16.6))
    feat2[1.3].append(wedge(178.6, 181.4, zc + 18, zc + 23))
    for a in (118, 242):                                   # two side airlocks
        sph_hatch(feat2, clear, 4.6, 52, a)
    grooves = [zslab(10.0, 10.8) - cockpit, zslab(21.0, 21.8) - cockpit]
    m = crew_build(feat, clear, feat2, grooves) - crew_inner()
    # forward cockpit windows: five panes separated by 1.2 mm mullions
    panes = [box(5.5, 7.2, CREW_R, 7.75, -16.8 + i * 8.4, zc + 10 + CREW_R / 2) for i in range(5)]
    m += box(1.9, 1.8, 4.0, -(CREW_R - CREW_WALL) + 0.75, 0, 2.0)          # alignment rib, ship underside
    return m - union(panes)


def crew_rear():
    """Rear hemisphere. Print coords: +z = ship aft, -x = ship up."""
    zc = CREW_CYL
    feat, feat2, clear = defaultdict(list), defaultdict(list), []
    feat[0.6].append(zslab(0, 2.0))
    crew_plating(feat, REAR_BANDS)
    crew_conduits(feat, 28.0, 9, 12)
    for a in (90, 270):                                    # large side airlocks
        sph_hatch(feat2, clear, 5.8, 58, a)
    sph_hatch(feat2, clear, 4.2, 40, 0)                    # ventral service hatch
    clear.append(wedge(166.5, 193.5, zc + 11, zc + 23))    # dorsal door
    feat2[0.9].append(wedge(168, 192, zc + 12, zc + 22))
    feat2[0.45].append(wedge(166.9, 193.1, zc + 11.2, zc + 22.8))
    feat2[1.3].append(wedge(178.6, 181.4, zc + 14, zc + 20))
    grooves = [zslab(10.0, 10.8), zslab(21.0, 21.8)]
    sphere = crew_build(feat, clear, feat2, grooves) - crew_inner()
    sphere += box(1.9, 1.8, 4.0, (CREW_R - CREW_WALL) - 0.75, 0, 2.0)       # alignment rib, ship underside
    sphere = sphere.scale([CREW_SCALE] * 3)
    rs = CREW_RS

    def dome(r):                                                          # height of the scaled sphere at radius r
        return math.sqrt(rs * rs - r * r)

    z_neck0 = rs - 2.0
    z_top = rs + NECK_L - 2.0
    body = [sphere]
    body.append(cyl(z_top - z_neck0, NECK_R, seg=64, z=z_neck0))
    body.append(cyl(dome(0) - dome(NECK_R + 5.0) + 2.0, NECK_R + 5.0, NECK_R, seg=64, z=dome(NECK_R + 5.0) - 0.6))  # fillet cone
    body.append(cyl(1.2, NECK_R + 0.6, seg=64, z=z_top - 4.0))            # neck collars
    body.append(cyl(1.0, NECK_R + 0.6, seg=64, z=z_top - 7.0))
    r0, r1 = NECK_R - 0.5, NECK_R + 9.0
    for k in range(8):                                                    # gusset ribs around the neck
        pts = [(r, y, z) for y in (-0.5, 0.5)
               for r, z in ((r0, dome(r0) - 0.8), (r1, dome(r1) - 0.8), (r0, dome(r0) + 7.0))]
        body.append(rz(Manifold.hull_points(pts), 45 * k + 22.5))
    lg, lg_hole = lug(NECK_R, z_neck0 + 5.0, length=9.0)
    body.append(rz(lg, 180))
    m = union(body) - rz(lg_hole, 180)
    m -= rz(core_bore(z_top + 1), 180)                                       # rod + wire channel (upper side = print -x)
    m -= cyl(PLUG_L + 0.6, PLUG_D / 2 + CLEAR, seg=64, z=z_top - PLUG_L - 0.5)  # socket
    m -= rz(socket_key(z_top - PLUG_L - 0.5, PLUG_L + 0.6), 180)             # keyway on the ship's upper side
    return m, z_top


COCK_DECK = -6.0      # cockpit floor height relative to the ship axis
COCK_BACK = 6.0       # distance of the rear bulkhead from the sphere centre


def cockpit_interior():
    k = CREW_SCALE
    m = _cockpit_interior().scale([k] * 3)
    return m - xcyl(8, LED_D / 2, k * COCK_BACK - 2, 32).translate([0, 0, k * (-COCK_DECK + 15.5)])   # LED seat above the door


def _cockpit_interior():
    """Cockpit insert for the front hemisphere. Print coords: z = up (deck on the bed),
    x = ship forward, y = sideways. Slides in from the open side and is glued in place."""
    up0 = -COCK_DECK                                       # print z of the ship axis
    r_in = CREW_R - CREW_WALL - 0.35
    parts, cuts = [], []
    parts.append(box(80, 80, 1.5, 0, 0, 0.75))                                   # deck
    parts.append(box(1.5, 80, 26.5, COCK_BACK + 0.75, 0, 13.25))                 # rear bulkhead
    # instrument console following the hull below the windows: hood + desk
    arc = wedge(-41, 41, 1.4, 9.8)
    parts.append((cyl(9.8, 33.4, seg=128) - cyl(12, 29.0, seg=128, z=-1)) ^ arc)
    parts.append((cyl(7.5, 29.5, seg=128) - cyl(12, 26.2, seg=128, z=-1)) ^ wedge(-39, 39, 1.4, 7.5))
    for a in (-30, -18, -6, 6, 18, 30):                                          # screens on the hood
        parts.append(rz(box(0.9, 4.6, 1.7, 29.0, 0, 8.75), a))
        cuts.append(rz(box(0.5, 3.8, 1.1, 28.55, 0, 8.75), a))
    for row, r in enumerate((27.0, 28.3)):                                       # switches on the desk
        for a in range(-36, 37, 3):
            if rng.random() < 0.7:
                parts.append(rz(box(0.8, 0.8, rng.choice([0.5, 0.7, 0.9]), r, 0, 7.6), a + row * 1.5))
    for sy in (-1, 1):
        y = sy * 7.5
        parts.append(box(5.5, 5.5, 2.8, 15.75, y, 2.8))                          # seat cushion
        parts.append(box(1.7, 5.5, 10.3, 12.35, y, 6.55))                        # backrest
        parts.append(box(1.9, 3.2, 2.0, 12.45, y, 12.6))                         # headrest
        for a in (-1, 1):                                                        # armrests
            parts.append(box(4.6, 0.8, 4.8, 15.3, y + a * 2.95, 3.8))
        cuts.append(box(0.4, 4.3, 8.0, 13.2, y, 7.2))                            # padding seams
        for dz in (5.0, 7.5, 10.0):
            cuts.append(box(0.5, 5.6, 0.35, 13.2, y, dz))
        parts.append(cyl(5.2, 0.6, seg=16, z=1.4).translate([23.5, y, 0]))       # control column
        parts.append(box(0.8, 3.4, 0.9, 23.5, y, 6.9))
        parts.append(box(0.8, 0.8, 1.4, 23.5, y - 1.3, 7.6))
        parts.append(box(0.8, 0.8, 1.4, 23.5, y + 1.3, 7.6))
    parts.append(box(10.5, 3.0, 3.8, 19.5, 0, 3.3))                              # centre pedestal
    for x in (15.5, 17.2, 18.9, 20.6, 22.3):
        parts.append(box(1.0, 2.0, 0.6, x, 0, 5.3))
    parts.append(box(0.8, 1.0, 2.2, 21.0, 0, 6.2))                               # throttle lever
    # rear bulkhead: door, equipment racks, lockers
    xb = COCK_BACK + 1.5
    parts.append(box(0.9, 8.0, 13.0, xb + 0.35, 0, 8.0) - box(1.0, 6.4, 11.4, xb + 0.75, 0, 8.0))
    cuts.append(box(0.6, 3.0, 2.2, xb + 0.2, 0, 11.0))                           # door window
    parts.append(box(0.6, 0.6, 2.0, xb + 0.45, 2.2, 7.0))                        # door handle
    for sy in (-1, 1):
        for i, (yc, w) in enumerate(((7.6, 5.0), (13.6, 5.4), (20.0, 6.0), (26.5, 5.0))):
            z0 = 1.6
            while z0 < 20.0 - i * 3.5:
                h = rng.uniform(3.0, 6.5)
                parts.append(box(rng.choice([0.5, 0.8, 1.1]) * 2, w - 0.6, h - 0.5, xb, sy * yc, z0 + h / 2))
                if rng.random() < 0.5:
                    parts.append(box(2.8, 1.0, 1.0, xb, sy * yc + rng.uniform(-1, 1), z0 + h / 2))
                z0 += h
    for y in range(-28, 29, 4):                                                  # deck plating seams
        cuts.append(box(60, 0.4, 0.6, 30, y, 1.5))
    for x in (10.5, 14.5, 19.0, 23.5):
        cuts.append(box(0.4, 80, 0.6, x, 0, 1.5))
    m = union(parts) - union(cuts)
    # trim to the inside of the hull so the insert slides in from the open side
    m ^= Manifold.sphere(r_in, 128).translate([0, 0, up0])
    m ^= xcyl(60, 32.2, 0, 128).translate([0, 0, up0])
    return m.trim_by_plane([1, 0, 0], COCK_BACK).trim_by_plane([0, 0, 1], 0)


def crew_joiner():
    return _crew_joiner().scale([CREW_SCALE] * 3)


def _crew_joiner():
    r = math.sqrt((CREW_R - CREW_WALL) ** 2 - 16.0) - CLEAR   # fits 4 mm into each half
    return cyl(8, r) - cyl(9, r - 1.2, z=-0.5) - box(4.0, 2.4, 10, r - 0.6, 0, 4.0)   # slot for the alignment ribs


# ----------------------------------------------------------------------- spine
def pod(z0, length, width, height):
    """Tank pod on the +x flat; both ends slope 45 deg so it prints unsupported."""
    r0 = SPINE_R * math.cos(math.radians(22.5)) - 0.9
    base = box(0.02, width, length, r0, 0, z0 + length / 2)
    top = box(0.02, width - 1.5, length - 2 * height, r0 + height, 0, z0 + length / 2)
    body = hull(base, top)
    top_l = length - 2 * height
    extra = []
    for _ in range(4):                                     # small equipment boxes on top
        w, l = rng.uniform(1.4, 3.6), rng.uniform(1.4, 4.5)
        extra.append(box(2 * rng.choice([0.4, 0.6, 0.9]), w, l, r0 + height,
                         rng.uniform(-(width - 1.5 - w) / 2, (width - 1.5 - w) / 2),
                         z0 + length / 2 + rng.uniform(-(top_l - l) / 2, (top_l - l) / 2)))
    m = union([body] + extra)
    for dz in (-top_l / 2 + 0.2, top_l / 2 - 0.2):         # panel grooves across the pod
        m -= box(0.9, width + 1, 0.45, r0 + height, 0, z0 + length / 2 + dz)
    return m


def spine_tank(z0, length=24.0):
    """Large pressure tank on the +x flat, with fairing, straps and feed pipes."""
    ap = SPINE_R * math.cos(math.radians(22.5))
    r, xc = 3.2, ap + 2.2
    zb, zt = z0 + r + 2.2 + 0.9, z0 + length - 3.0
    parts = [cyl(zt - zb, r, seg=32, z=zb).translate([xc, 0, 0]),
             hull(cyl(0.05, r, seg=32, z=zb).translate([xc, 0, 0]), box(0.02, 2.0, 0.02, ap - 0.3, 0, z0 + 0.3)),
             cyl(r * 0.8, r, r * 0.4, seg=32, z=zt - 0.01).translate([xc, 0, 0]),
             cyl(1.0, 0.9, seg=16, z=zt + r * 0.8 - 0.05).translate([xc, 0, 0])]
    for f in (0.2, 0.5, 0.8):
        parts.append(cyl(0.7, r + 0.35, seg=32, z=zb + (zt - zb) * f).translate([xc, 0, 0]))
    for sy in (-1, 1):
        parts.append(cyl(length, 0.5, seg=12, z=z0).translate([ap + 0.25, sy * 2.5, 0]))
    return union(parts)


def spine_fin(z0, length=24.0):
    """Radiator fin on the +x flat; both ends slope 45 deg."""
    ap = SPINE_R * math.cos(math.radians(22.5))
    fin = hull(box(0.02, 0.9, length, ap - 0.3, 0, z0 + length / 2),
               box(0.02, 0.9, length - 11.5, ap + 5.5, 0, z0 + length / 2))
    ribs = [box(5.0, 1.5, 0.5, ap + 2.4, 0, z0 + length / 2 + dz) for dz in (-3.5, 0, 3.5)]
    return union([fin] + ribs)


def spine_drum(z0, length=24.0):
    """Wider module with airlocks and equipment on its eight faces."""
    rd = SPINE_R + 4.5
    body = hull(octa(0.05, SPINE_R, z=z0), octa(length - 9.0, rd, z=z0 + 4.5), octa(0.05, SPINE_R, z=z0 + length - 0.05))
    adds, cuts = [body], []
    for k in range(8):
        a, c = detail_face(rd * math.cos(math.radians(22.5)), 2 * rd * math.sin(math.radians(22.5)) - 1.0,
                           z0 + 5.0, z0 + length - 5.0, 45 * k)
        adds += a
        cuts += c
    return adds, cuts


def spine_segment(kinds, antenna_hole=False, lug_at=None):
    ap = SPINE_R * math.cos(math.radians(22.5))
    parts = [octa(SEG_L, SPINE_R), cyl(PLUG_L, PLUG_D / 2, seg=64, z=SEG_L - 0.01), plug_key(SEG_L - 0.01)]
    cuts = []
    z = 20.0
    for i, kind in enumerate(kinds):
        parts.append(octa(1.6, SPINE_R + 0.8, z=z - 3.8))                # collar ring below each cluster
        if kind == "pods":
            for k in range(4):
                parts.append(rz(pod(z, 24.0, 9.0, 6.0), k * 90 + (45 if i % 4 else 0)))
        elif kind == "tanks":
            for k in range(4):
                parts.append(rz(spine_tank(z), k * 90))
        elif kind == "fins":
            for k in range(8):
                parts.append(rz(spine_fin(z), k * 45))
            parts.append(octa(1.2, SPINE_R + 1.0, z=z + 11.4))
        elif kind == "drum":
            a, c = spine_drum(z)
            parts += a
            cuts += c
        z += 30.0
    for k in range(8):                                     # conduits along the eight edges
        a = math.radians(22.5 + 45 * k)
        parts.append(cyl(SEG_L, 0.7, seg=12).translate([(SPINE_R - 0.25) * math.cos(a), (SPINE_R - 0.25) * math.sin(a), 0]))
    w_face = 2 * SPINE_R * math.sin(math.radians(22.5)) - 0.9
    for k in range(8):                                     # kit detail on the free ends of the core
        for za, zb in ((1.5, 15.5), (z - 4.0, SEG_L - 1.5)):
            if k == 0 and ((antenna_hole and za < 5) or (lug_at is not None and za > 5)):
                continue
            a, c = detail_face(ap, w_face, za, zb, 45 * k)
            parts += a
            cuts += c
    m = union(parts)
    if cuts:
        m -= union(cuts)
    m -= core_bore(SEG_L + PLUG_L + 2, -1)
    m -= cyl(PLUG_L + 0.6, PLUG_D / 2 + CLEAR, seg=64, z=-0.1)
    m -= socket_key(-0.1, PLUG_L + 0.6)
    if lug_at is not None:
        lg, lg_hole = lug(ap, lug_at)
        m = (m + lg) - lg_hole
    if antenna_hole:
        m -= cyl(MAST_PIN + 1, 2.0 + CLEAR, seg=32).rotate([0, 90, 0]).translate([ap - MAST_PIN, 0, 12.0])
        m -= cyl(ap, 0.8, seg=16).rotate([0, 90, 0]).translate([0, 0, 12.0])      # antenna wires into the spine channel
    return m


def dish(r, stem_r, z0):
    """Conical dish opening upward (45 deg wall, prints without support) with a feed horn."""
    h = r - stem_r
    shell = cyl(h, stem_r, r, seg=96, z=z0) - cyl(h, stem_r, r, seg=96, z=z0 + 1.1)
    rim = cyl(0.8, r + 0.5, seg=96, z=z0 + h - 0.8) - cyl(2, r - 0.3, seg=96, z=z0 + h - 1.4)
    horn = cyl(h * 0.6, 0.9, seg=24, z=z0 + 0.5)
    tip = cyl(1.2, 1.5, seg=24, z=z0 + h * 0.6 + 0.4)
    return union([shell, rim, horn, tip]).trim_by_plane([0, 0, -1], -(z0 + h))


AX_Z = 3.2            # hinge axis height in the dish carrier (print coords)
TOWER_TOP = 34.0      # height of the tower tip above the hinge (carries the larger red LED)
BAR_HALF = 43.0       # half length of the cross bar (small red LEDs at both ends)


def led_post(height, r_out, r_pocket):
    """Post with a pocket on top for a pre-wired SMD LED and a wire bore down to the back."""
    post = cyl(height, r_out + 0.5, r_out, seg=32)
    return post, cyl(1.3, r_pocket, seg=24, z=height - 1.2), cyl(height + 2, 0.45, seg=16, z=0.5)


def antenna_dishes():
    """Large dish in the middle, a small dish on each side, on a tilting carrier.
    Three red LEDs: a larger one on the tower tip, two small ones at the ends of the cross bar.
    Print coords: +z = ship forward (dishes open upward), +x = ship up, hinge along y."""
    xb = 7.8
    parts = [box(6, 6, 6.4, 0, 0, 3.2), box(3.0, 6, 6.4, 4.4, 0, 3.2),              # hub + web
             box(4.0, 2 * BAR_HALF, 4.0, xb, 0, 2.0),                               # cross bar
             box(TOWER_TOP - xb + 2.0, 4.0, 4.0, (TOWER_TOP + xb) / 2 + 1.0, 0, 2.0)]  # tower behind the big dish
    for y, r, sr in ((0, 19.0, 2.0), (-29, 9.0, 1.4), (29, 9.0, 1.4)):
        parts.append(cyl(3.2, sr + 0.6, sr, seg=32, z=3.9).translate([xb, y, 0]))
        parts.append(dish(r, sr, 7.0).translate([xb, y, 0]))
    for y in (-14.5, 14.5):                                  # small equipment boxes on the bar
        parts.append(box(3.0, 5, 1.2, xb, y, 4.5))
    cuts = []
    for x, y, h, ro, rp in ((TOWER_TOP, 0, 8.0, 2.3, 1.6), (xb, -BAR_HALF + 2.0, 11.0, 1.9, 1.2), (xb, BAR_HALF - 2.0, 11.0, 1.9, 1.2)):
        post, pocket, bore = led_post(h, ro, rp)
        parts.append(post.translate([x, y, 0]))
        cuts += [pocket.translate([x, y, 0]), bore.translate([x, y, 0])]
    m = union(parts) - union(cuts)
    m -= cyl(10, 1.1, seg=24, z=-5).rotate([90, 0, 0]).translate([0, 0, AX_Z])   # hinge bore (1.75 mm filament)
    m -= box(1.4, 2 * BAR_HALF - 4.6, 1.8, xb, 0, 0)         # wire groove on the back of the bar
    m -= box(TOWER_TOP + 3.9, 1.4, 1.8, (TOWER_TOP + 0.7 - 3.2) / 2, 0, 0)  # ... along the tower and down to the hinge
    return m


MAST_AX = 4.0         # hinge axis height above the arm tips (mast is printed upside down)
MAST_PIN = 3.0        # length of the pin that sits in the spine (stays clear of the wire channel)
MAST_H = 26.5 + MAST_PIN


def antenna_mast():
    """Mast with fork. Printed upside down: fork arms on the bed, pin on top."""
    arms = [box(6, 2.0, 9.05, 0, sy * 4.25, 4.525) for sy in (-1, 1)]
    bridge = box(6, 10.5, 2.5, 0, 0, 10.25)
    col = cyl(15.0, 3.0, seg=48, z=11.49)
    collar = cyl(1.2, 3.8, seg=48, z=24.0)
    pin = cyl(MAST_PIN, 2.0, seg=48, z=26.49)
    m = union(arms + [bridge, col, collar, pin])
    m -= cyl(14, 0.95, seg=24, z=-7).rotate([90, 0, 0]).translate([0, 0, MAST_AX])  # press fit for the filament pin
    m -= cyl(23.0, 0.65, seg=16, z=8.9)                      # wire channel from the fork down through the pin
    return m


# ------------------------------------------------------------- reactor / engines
Z_T0 = ENG_L                 # start of transition
Z_OCT = ENG_L + 12.0         # start of octagonal block
Z_TOP = Z_OCT + BLOCK_L      # open top (front of block)
Z_FLOOR = Z_OCT + 3.0        # cavity floor
Z_BAY = Z_TOP - 12.75        # centre of the switch cutout
Z_TRAY0 = Z_FLOOR + 6.0 + 8.0   # rear end of the battery tray opening (above the housing lip)
Z_TRAY1 = Z_TRAY0 + TRAY_L
Z_PIN = Z_TRAY0 + 5.0
X_PIN = TRAY_CUT + 2.0
Z_LUG = Z_OCT + BLOCK_L / 2 - 5.0


def engine_block():
    # six nozzles: three columns side by side (print y), two stacked per column (print x = ship up)
    corners = [(sx * ENG_OFF, c * ENG_COL) for sx in (-1, 1) for c in (-1, 0, 1)]
    hx, hy = ENG_OFF + ENG_R, ENG_COL + ENG_R

    def rsq(h, z):
        return hull(*[cyl(h, ENG_R, seg=64, z=z).translate([x, y, 0]) for x, y in corners])

    housing = rsq(ENG_L, 0)
    trans = hull(rsq(0.1, Z_T0 - 0.1), octa(0.1, BLOCK_R, z=Z_OCT))
    block = octa(BLOCK_L + 0.05, BLOCK_R, z=Z_OCT)
    ap = BLOCK_R * math.cos(math.radians(22.5))
    half_w = BLOCK_R * math.sin(math.radians(22.5))

    def skip(k, t, z, w, l):  # keep the stand socket area clean (face 4 = -x)
        return False

    gre, kit_cuts = [], []

    def add_face(*args, **kw):
        a, c = detail_face(*args, **kw)
        gre.extend(a)
        kit_cuts.extend(c)

    for k in range(8):                                     # reactor block: eight detailed faces
        blank = None
        if k == 4:                                         # keep the switch / USB area clear
            blank = lambda t, z, w, l: z + l > Z_TRAY0 - 1
        if k in (3, 5):                                    # tray reaches into the two lower diagonal faces
            blank = lambda t, z, w, l: z < Z_TRAY1 + 1 and z + l > Z_TRAY0 - 1
        if k == 0:                                         # keep the suspension lug area clear
            blank = lambda t, z, w, l: z < Z_LUG + 12 and z + l > Z_LUG - 10
        add_face(ap, 2 * half_w - 1.6, Z_OCT + 3.2, Z_TOP - 3.2, 45 * k, blank=blank)
    for za, zb in ((0.6, 13.4), (15.8, ENG_L - 0.5)):      # engine housing, above and below the belt groove
        for ang in (0, 180):
            for c in (-1, 0, 1):
                add_face(hx, 14.4, za, zb, ang, t0=c * 15.3)
        for ang in (90, 270):
            for c in (-1, 1):
                add_face(hy, 9.6, za, zb, ang, t0=c * 5.8)
    for k in range(8):                                     # conduits along the block edges
        a = math.radians(22.5 + 45 * k)
        gre.append(cyl(BLOCK_L - 4.0, 0.9, seg=12, z=Z_OCT + 2.0)
                   .translate([(BLOCK_R - 0.3) * math.cos(a), (BLOCK_R - 0.3) * math.sin(a), 0]))
    rings = [octa(1.6, BLOCK_R + 0.7, z=Z_OCT + 1.0), octa(1.6, BLOCK_R + 0.7, z=Z_TOP - 2.6)]
    m = union([housing, trans, block] + gre + rings)

    # engine housing detail: side grooves + one belt groove
    cuts = list(kit_cuts)
    for sx in (-1, 1):                                     # grooves between the nozzle columns
        for y in (-7.65, 7.65):
            cuts.append(box(2.0, 0.9, ENG_L + 2, sx * hx, y, ENG_L / 2))
    for sy in (-1, 1):
        cuts.append(box(0.9, 2.0, ENG_L + 2, 0, sy * hy, ENG_L / 2))
    belt = rsq(1.2, 14.0).scale([1.08, 1.08, 1]) - rsq(1.4, 13.9).scale([(hx - 0.9) / hx, (hy - 0.9) / hy, 1])
    cuts.append(belt)
    for x, y in corners:                                   # engraved rings on the rear face
        cuts.append((cyl(0.45, 9.7, seg=64, z=-0.01) - cyl(1, 9.2, seg=64, z=-0.3)).translate([x, y, 0]))
    cuts.append(box(0.5, 2 * hy, 0.9, 0, 0, 0))
    for y in (-ENG_COL / 2, ENG_COL / 2):
        cuts.append(box(2 * hx, 0.5, 0.9, 0, y, 0))
    # interior
    cuts.append(octa(BLOCK_L, BLOCK_CAV_R, z=Z_FLOOR))
    for x, y in corners:
        z_led1 = NOZ_PLUG_L + NOZ_PLUG_R + CLEAR - NOZ_WIRE_R + 3.4
        rs = NOZ_PLUG_R + CLEAR
        cuts.append(cyl(NOZ_PLUG_L + 0.21, rs, seg=48, z=-0.01).translate([x, y, 0]))             # nozzle socket
        cuts.append(cyl(rs - NOZ_WIRE_R, rs, NOZ_WIRE_R, seg=48, z=NOZ_PLUG_L + 0.19).translate([x, y, 0]))
        cuts.append(cyl(4.0, NOZ_WIRE_R, seg=32, z=NOZ_PLUG_L + rs - NOZ_WIRE_R).translate([x, y, 0]))  # wire passage
        y_top = y * 13.5 / ENG_COL                         # outer bores slant inward to reach the cavity
        cuts.append(hull(cyl(0.5, 3.25, seg=32, z=z_led1).translate([x, y, 0]),
                         cyl(0.5, 3.25, seg=32, z=Z_FLOOR).translate([x, y_top, 0])))             # wire bore
    m -= union(cuts)

    # electronics bay: rocker switch and USB-C charging port on the underside (print -x)
    xw = -BLOCK_R * math.cos(math.radians(22.5))
    m -= box(6, SWITCH_CUT[0], SWITCH_CUT[1], xw, 0, Z_BAY)
    m += box(0.8, 12.6, 0.8, xw, 0, Z_BAY - 8.6) + box(0.8, 12.6, 0.8, xw, 0, Z_BAY + 8.6)          # switch guard rails
    # battery tray opening: everything below TRAY_CUT between Z_TRAY0 and Z_TRAY1
    m -= box(40, 80, TRAY_L, TRAY_CUT - 20, 0, (Z_TRAY0 + Z_TRAY1) / 2)
    m -= cyl(70, PIN_D / 2 + 0.08, seg=16, z=-35).rotate([90, 0, 0]).translate([X_PIN, 0, Z_PIN])    # locking pin holes
    # suspension lug on the upper side (print +x)
    lg, lg_hole = lug(-xw, Z_LUG)
    m = (m + lg) - lg_hole
    return m - box(6.0, 4.2, 4.4, -xw, 0, Z_TOP - 2.1)      # notch for the adapter tooth (upper side)


def battery_tray():
    """Removable belly pan of the reactor block. The 18650 holder is glued into it, so the cell
    comes out with the tray. A wedge tongue hooks under the front edge, a filament pin locks the rear.
    Built in block coordinates; exported lying on its flat underside."""
    g = 0.2                                                   # clearance to the opening
    shell = octa(BLOCK_L, BLOCK_R, z=Z_OCT) - octa(BLOCK_L + 2, BLOCK_CAV_R, z=Z_OCT - 1)
    tray = shell ^ box(40, 80, TRAY_L - 2 * g, TRAY_CUT - g - 20, 0, (Z_TRAY0 + Z_TRAY1) / 2)
    xi = -BLOCK_CAV_R * math.cos(math.radians(22.5))          # inner face of the underside wall
    tongue = hull(box(1.4, 12, 3.8, xi + 0.7, 0, Z_TRAY1 - g - 1.9),
                  box(1.2, 12, 0.1, xi + 3.0, 0, Z_TRAY1 + 1.95))
    parts = [tray, tongue]
    cuts = []
    for sy in (-1, 1):                                        # lugs for the locking pin
        parts.append(box(X_PIN + 3.0 - (xi + 6.0), 2.0, 6.0, (X_PIN + 3.0 + xi + 6.0) / 2, sy * 16.5, Z_PIN))
    cuts.append(cyl(70, PIN_D / 2 + 0.22, seg=16, z=-35).rotate([90, 0, 0]).translate([X_PIN, 0, Z_PIN]))
    for z in (Z_TRAY0 + 16, Z_TRAY0 + 42, Z_TRAY0 + 68):      # panel seams across the underside
        cuts.append(box(0.5, 16, 0.5, -BLOCK_R * math.cos(math.radians(22.5)), 0, z))
    cuts.append(box(1.2, 8, 3.0, -BLOCK_R * math.cos(math.radians(22.5)), 0, Z_TRAY0 + 3.5))   # fingernail recess
    return union(parts) - union(cuts)


Z_SPLIT = Z_FLOOR + 6.0      # the block is printed as two parts, split here


def split_block(blk):
    """Engine housing (lower) with a keyed lip, and the reactor tube (upper), printed split face down."""
    r_lip = BLOCK_CAV_R - 0.2
    lower = blk.trim_by_plane([0, 0, -1], -Z_SPLIT)
    lip = octa(6.0, r_lip, z=Z_SPLIT - 0.05) - octa(8.0, r_lip - 1.6, z=Z_SPLIT - 1.0)
    lip -= box(6.0, 8.0, 8.0, -r_lip * math.cos(math.radians(22.5)), 0, Z_SPLIT + 3.0)     # gap for the key tab
    upper = blk.trim_by_plane([0, 0, 1], Z_SPLIT).translate([0, 0, -Z_SPLIT])
    ap_c = BLOCK_CAV_R * math.cos(math.radians(22.5))
    upper += box(1.6, 6.0, 6.2, -ap_c + 0.7, 0, 3.1)                                       # key tab (ship underside)
    return lower + lip, upper


def bell_r(x):
    """Inner radius of the bell, x = distance from the throat (38 deg at throat, 10 deg at exit)."""
    a, e = math.tan(math.radians(38)), math.tan(math.radians(10))
    return NOZ_RT + a * x + (e - a) / (2 * NOZ_L) * x * x


def nozzle():
    """Bell nozzle, printed rim down. The plug on top goes into the engine housing."""
    n = 40
    zs = [NOZ_L * i / n for i in range(n + 1)]                       # print z, rim at z = 0
    prof = [(bell_r(NOZ_L - z), z) for z in zs]
    z1, z2 = NOZ_L + NOZ_FLANGE, NOZ_L + NOZ_FLANGE + NOZ_PLUG_L
    ro_t = NOZ_RT + NOZ_WALL
    outer_pts = [(0, 0)] + [(r + NOZ_WALL, z) for r, z in prof] + \
                [(ro_t + 2.0, NOZ_L + 2.0), (ro_t + 2.0, z1), (NOZ_PLUG_R, z1), (NOZ_PLUG_R, z2), (0, z2)]
    z_sh = NOZ_L - NOZ_LED_OUT + 4.3                                 # shoulder for the LED flange (LED body = 4.3 mm)
    inner_pts = [(0, -1)] + [(prof[0][0], -1)] + prof + [(NOZ_RT, z_sh), (2.05, z_sh), (2.05, z2 + 1), (0, z2 + 1)]
    outer = Manifold.revolve(CrossSection([outer_pts]), 96)
    inner = Manifold.revolve(CrossSection([inner_pts]), 96)
    rings = [cyl(1.0, prof[0][0] + NOZ_WALL + 0.45, seg=96)]          # rim band
    for z in (4.5, 8.5, 12.0):                                        # stiffening hoops
        rings.append(cyl(0.7, bell_r(NOZ_L - z) + NOZ_WALL + 0.4, bell_r(NOZ_L - z - 0.7) + NOZ_WALL + 0.4, seg=96, z=z))
    for k in range(8):                                                # bolts on the flange
        a = math.radians(45 * k)
        rings.append(cyl(1.0, 0.55, seg=12, z=NOZ_L + 1.6).translate([(ro_t + 2.0) * math.cos(a), (ro_t + 2.0) * math.sin(a), 0]))
    return union([outer] + rings) - inner


def adapter():
    """Tapered collar between spine and block. Printed wide side down."""
    rl = BLOCK_CAV_R - 0.2
    lip = octa(4.1, rl)
    body = hull(octa(0.05, rl, z=4.0), octa(1.8, BLOCK_R, z=6.2), octa(0.05, SPINE_R + 0.5, z=29.95))
    plug = cyl(PLUG_L, PLUG_D / 2, seg=64, z=29.99) + plug_key(29.99)
    ap_l = rl * math.cos(math.radians(22.5))
    tooth = box(BLOCK_R * math.cos(math.radians(22.5)) - ap_l + 0.1, 3.8, 4.1, (BLOCK_R * math.cos(math.radians(22.5)) + ap_l) / 2, 0, 2.05)
    ribs = [rz(hull(box(1.4, 1.6, 0.1, BLOCK_R * 0.92 - 0.3, 0, 8.0), box(1.4, 1.6, 0.1, SPINE_R * 0.92 + 0.6, 0, 29.9)),
               k * 45) for k in range(8)]
    m = union([lip, body, plug, tooth] + ribs)
    m -= hull(octa(6.1, rl - 1.6, z=-0.1), octa(0.05, 3.0, z=27.0))
    m -= core_bore(40)
    return m


# ---------------------------------------------------------------------- stands
# ------------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    front = crew_front()
    rear, neck_top = crew_rear()
    join = crew_joiner()
    segs = [spine_segment(["pods", "tanks", "pods"]),
            spine_segment(["drum", "pods", "fins"], antenna_hole=True),
            spine_segment(["pods", "fins", "pods"], lug_at=SEG_L - 14.0),
            spine_segment(["tanks", "pods", "drum"])]
    dishes = antenna_dishes()
    mast = antenna_mast()
    adp = adapter()
    blk = engine_block()
    housing, reactor = split_block(blk)
    tray = battery_tray()
    ap_b = BLOCK_R * math.cos(math.radians(22.5))
    tray_print = tray.translate([0, 0, -Z_TRAY0]).rotate([0, -90, 0]).translate([0, 0, ap_b])
    noz = nozzle()
    cock = cockpit_interior()

    for m, n in [(front, "01_crew_front.stl"), (rear, "02_crew_rear.stl"), (join, "03_crew_joiner_ring.stl"),
                 (cock, "04_cockpit_interior.stl"),
                 (segs[0], "05_spine_A.stl"), (segs[1], "06_spine_B_antenna.stl"),
                 (segs[2], "07_spine_C_lug.stl"), (segs[3], "08_spine_D.stl"),
                 (adp, "09_adapter_collar.stl"), (reactor, "10_reactor_block.stl"),
                 (housing, "11_engine_housing.stl"), (noz, "12_engine_nozzle_6x.stl"),
                 (dishes, "13_antenna_dishes.stl"), (mast, "14_antenna_mast.stl"),
                 (tray_print, "15_battery_tray.stl")]:
        write_stl(m, n)

    # ---- assembled preview (ship axis = x, nose at x = 0, +z = up)
    def fwd(m, c):   # print z -> ship -x
        return m.rotate([0, -90, 0]).translate([c, 0, 0])

    def aft(m, c):   # print z -> ship +x
        return m.rotate([0, 90, 0]).translate([c, 0, 0])

    ANT_SEG = 1                      # antenna sits at the rear end of the second segment
    x_mid = CREW_RS
    x1 = x_mid + neck_top            # neck end = start of spine
    x3 = x1 + N_SEG * SEG_L          # end of spine
    x4 = x3 + 30.0 - 4.0             # block front face (adapter lip sits 4 mm inside)
    ap = SPINE_R * math.cos(math.radians(22.5))
    xa = x1 + (ANT_SEG + 1) * SEG_L - 12.0
    za = ap - MAST_PIN + MAST_H - MAST_AX
    asm = [fwd(front, x_mid), aft(rear, x_mid)]
    asm += [fwd(segs[i], x1 + (i + 1) * SEG_L) for i in range(N_SEG)]
    xr = x4 + Z_TOP                  # rear face of the engine housing
    asm += [fwd(noz, xr + NOZ_L + NOZ_FLANGE).translate([0, c * ENG_COL, sx * ENG_OFF])
            for sx in (-1, 1) for c in (-1, 0, 1)]
    asm += [fwd(adp, x3 + 30.0), fwd(blk, x4 + Z_TOP),
            mast.rotate([180, 0, 0]).translate([xa, 0, ap - MAST_PIN + MAST_H]),
            fwd(dishes, xa + AX_Z).translate([0, 0, za])]
    cock_ship = cock.rotate([0, 0, 180]).translate([x_mid, 0, COCK_DECK * CREW_SCALE])
    print("cockpit vs hull overlap volume:", round((cock_ship ^ union(asm[:2])).volume(), 3))
    tray_ship = fwd(tray, x4 + Z_TOP)
    print("battery tray vs block overlap volume:", round((tray_ship ^ fwd(blk, x4 + Z_TOP)).volume(), 3))
    full = Manifold.compose(asm + [cock_ship, tray_ship])
    write_stl(full, "00_assembly_preview_only.stl")
    lugs_x = [x_mid + neck_top - NECK_L + 2.0 + 5.0 + 5.0, x1 + 3 * SEG_L - (SEG_L - 14.0 + 6.0), x4 + Z_TOP - (Z_LUG + 6.0)]
    print("suspension eyes at x =", [round(v) for v in lugs_x], "mm from the nose")
    if os.environ.get("EXPLODED"):                   # optional exploded view for the assembly guide
        import json
        ex = [("01", fwd(front, x_mid), -62), ("04", cock_ship, -30), ("03", fwd(join, x_mid + 4 * CREW_SCALE), -8), ("02", aft(rear, x_mid), 12)]
        ex += [("%02d" % (5 + i), fwd(segs[i], x1 + (i + 1) * SEG_L), 40 + 26 * i) for i in range(N_SEG)]
        ex += [("09", fwd(adp, x3 + 30.0), 146), ("10", fwd(reactor, x4 + Z_TOP - Z_SPLIT), 174),
               ("11", fwd(housing, x4 + Z_TOP), 206), ("15", tray_ship.translate([0, 0, -34]), 174)]
        labels, solids = [], []
        for name, m, dx in ex:
            m = m.translate([dx, 0, 0]); solids.append(m); b = m.bounding_box()
            labels.append([name, (b[0] + b[3]) / 2, 0, b[5] + 16])
        nz = [n.translate([240, 0, 0]) for n in asm[2 + N_SEG:8 + N_SEG]]
        solids += nz; labels.append(["12 (6x)", xr + 250, 0, 40])
        solids += [asm[-1].translate([66, 0, 62]), asm[-2].translate([66, 0, 26])]
        labels += [["13", xa + 40, 0, 150], ["14", xa + 96, 0, 62]]
        write_stl(Manifold.compose(solids), os.environ["EXPLODED"] + ".stl")
        json.dump(labels, open(os.path.join(OUT, os.environ["EXPLODED"] + ".json"), "w"))
    # joints: the two block halves must mate without interference
    print("housing vs reactor overlap volume:", round((housing ^ reactor.translate([0, 0, Z_SPLIT])).volume(), 3))
    print("adapter vs block overlap volume:", round((fwd(adp, x3 + 30.0) ^ fwd(blk, x4 + Z_TOP)).volume(), 3))
    print("spine joint overlap volume:", round((asm[2] ^ asm[3]).volume(), 3), "/ neck:", round((asm[1] ^ asm[2]).volume(), 3),
          "/ adapter:", round((asm[1 + N_SEG] ^ fwd(adp, x3 + 30.0)).volume(), 3))
    print(f"overall length: {xr + NOZ_L + NOZ_FLANGE:.0f} mm, sphere {2 * CREW_RS:.0f} mm, ratio 1:{(xr + NOZ_L + NOZ_FLANGE) / (2 * CREW_RS):.1f}")
    print("nozzles vs block overlap volume:", round((union(asm[2 + N_SEG:8 + N_SEG]) ^ fwd(blk, x4 + Z_TOP)).volume(), 3))
    # sanity: no part may intersect the antenna assembly or the spine it sits above
    others = union([a for i, a in enumerate(asm) if i not in (len(asm) - 2, len(asm) - 1)])
    print("dish carrier vs rest overlap volume:", round((asm[-1] ^ others).volume(), 3))
    print("dish carrier vs mast overlap volume:", round((asm[-1] ^ asm[-2]).volume(), 3))


if __name__ == "__main__":
    main()
