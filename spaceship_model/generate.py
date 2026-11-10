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
import struct

import numpy as np
from manifold3d import Manifold, OpType

# ----------------------------------------------------------------- parameters
CLEAR = 0.15          # radial clearance for plug/socket fits
LED_D = 3.2           # hole for a 3 mm LED
WIRE_D = 4.5          # wire channel through the spine
PLUG_D = 9.0          # spine connector plug diameter
PLUG_L = 8.0

CREW_R = 36.0         # crew module radius (sphere)
CREW_CYL = 0.0        # optional cylindrical stretch per half; 0 = pure sphere
CREW_WALL = 1.6
NECK_R = 8.0
NECK_L = 16.0

SPINE_R = 8.0         # circumradius of octagonal spine core
SEG_L = 140.0         # length of one spine segment

BLOCK_R = 25.0        # circumradius of octagonal reactor block
BLOCK_L = 70.0
BLOCK_CAV_R = 23.0
ENG_OFF = 11.5        # nozzle centre offset (2 x 2 cluster)
ENG_R = 10.0
ENG_L = 30.0
BELL_R = 8.5
BELL_D = 8.0

AXIS_H = 95.0         # height of ship axis above the table on its stands
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


def write_stl(m, name):
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


def face_greebles(apothem, half_w, z0, z1, n_per_face, faces=8, skip=None):
    """Random raised panels on the flats of a prism (print axis = z)."""
    out = []
    step = 360.0 / faces
    for k in range(faces):
        for _ in range(n_per_face):
            w = rng.uniform(2.0, min(9.0, 2 * half_w - 1))
            l = rng.uniform(2.5, 14.0)
            h = rng.choice([0.4, 0.6, 0.8])
            t = rng.uniform(-(half_w - w / 2 - 0.4), half_w - w / 2 - 0.4)
            z = rng.uniform(z0 + l / 2, z1 - l / 2)
            if skip and skip(k, t, z, w, l):
                continue
            out.append(rz(box(2 * h, w, l, apothem, t, z), k * step))
    return out


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


def crew_band(z, h=1.4, lift=0.5):
    """Raised belt following the hull between heights z and z+h."""
    return crew_shell(lift).trim_by_plane([0, 0, 1], z).trim_by_plane([0, 0, -1], -(z + h))


def crew_front():
    body = [crew_shell(), crew_band(0.0, 2.0), crew_band(13.0, 1.6), crew_band(30.0, 1.2)]
    # sensor ports on the dome and a nose cap
    for a in (30, 150, 270):
        port = cyl(4, 4.5, seg=48, z=CREW_R - 3.3).rotate([0, 50, 0])
        body.append(rz(port, a).translate([0, 0, CREW_CYL]))
    body.append(cyl(1.2, 6.5, seg=64, z=CREW_CYL + CREW_R - 0.6))
    body.append(cyl(1.8, 2.5, seg=32, z=CREW_CYL + CREW_R - 0.6))
    m = union(body)
    m -= crew_inner()
    # illuminated window band
    wins = [rz(box(6, 5.0, 3.0, CREW_R - 1, 0, 8.0), i * 360 / 16) for i in range(16)]
    return m - union(wins)


def crew_rear():
    body = [crew_shell(), crew_band(0.0, 2.0), crew_band(13.0, 1.6), crew_band(24.0, 1.2)]
    for i in range(22):  # panels on the cylindrical part
        a = rng.uniform(0, 360)
        slab = box(12, rng.uniform(3, 8), rng.uniform(2, 6), CREW_R - 4, 0, rng.uniform(4.5, 10))
        body.append(rz(slab, a) ^ crew_shell(0.5))
    z_neck0 = CREW_CYL + CREW_R - 2.0
    z_top = CREW_CYL + CREW_R + NECK_L - 2.0
    body.append(cyl(z_top - z_neck0, NECK_R, seg=64, z=z_neck0))
    body.append(cyl(3.0, NECK_R + 3.0, NECK_R, seg=64, z=z_neck0))  # fillet cone
    m = union(body)
    m -= crew_inner()
    m -= cyl(z_top + 1, WIRE_D / 2, seg=32)                                   # wire channel
    m -= cyl(PLUG_L + 0.6, PLUG_D / 2 + CLEAR, seg=64, z=z_top - PLUG_L - 0.5)  # socket
    return m, z_top


def crew_joiner():
    r = math.sqrt((CREW_R - CREW_WALL) ** 2 - 16.0) - CLEAR   # fits 4 mm into each half
    return cyl(8, r) - cyl(9, r - 1.2, z=-0.5)


# ----------------------------------------------------------------------- spine
def pod(z0, length, width, height):
    """Tank pod on the +x flat; both ends slope 45 deg so it prints unsupported."""
    r0 = SPINE_R * math.cos(math.radians(22.5)) - 0.9
    base = box(0.02, width, length, r0, 0, z0 + length / 2)
    top = box(0.02, width - 1.5, length - 2 * height, r0 + height, 0, z0 + length / 2)
    body = hull(base, top)
    cap = box(1.0, width - 4.5, (length - 2 * height) * 0.6, r0 + height, 0, z0 + length / 2)
    return body + cap


def spine_segment(antenna_hole=False):
    parts = [octa(SEG_L, SPINE_R), cyl(PLUG_L, PLUG_D / 2, seg=64, z=SEG_L - 0.01)]
    z = 20.0
    i = 0
    while z + 24 <= SEG_L - 4:
        for k in range(4):
            parts.append(rz(pod(z, 24.0, 9.0, 6.0), k * 90 + (45 if i % 2 else 0)))
        # collar ring between clusters
        parts.append(octa(1.6, SPINE_R + 0.8, z=z - 3.8))
        z += 30.0
        i += 1
    m = union(parts)
    m -= cyl(SEG_L + PLUG_L + 2, WIRE_D / 2, seg=32, z=-1)
    m -= cyl(PLUG_L + 0.6, PLUG_D / 2 + CLEAR, seg=64, z=-0.1)
    if antenna_hole:
        ap = SPINE_R * math.cos(math.radians(22.5))
        m -= cyl(3.5 + 1, 1.65, seg=32).rotate([0, 90, 0]).translate([ap - 3.5, 0, 12.0])
    return m


def antenna():
    stem = cyl(13, 1.5, seg=32)
    outer = cyl(15.5, 1.5, 17.0, seg=96, z=12)
    inner = cyl(15.5, 1.5, 17.0, seg=96, z=13.1)
    dish = outer - inner
    horn = cyl(9, 1.0, seg=24, z=12.5)
    return union([stem, dish, horn]).trim_by_plane([0, 0, -1], -27.5)


# ------------------------------------------------------------- reactor / engines
Z_T0 = ENG_L                 # start of transition
Z_OCT = ENG_L + 5.0          # start of octagonal block
Z_TOP = Z_OCT + BLOCK_L      # open top (front of block)
Z_FLOOR = Z_OCT + 3.0        # cavity floor
Z_STAND = Z_OCT + BLOCK_L / 2


def engine_block():
    corners = [(sx * ENG_OFF, sy * ENG_OFF) for sx in (-1, 1) for sy in (-1, 1)]

    def rsq(h, z):
        return hull(*[cyl(h, ENG_R, seg=64, z=z).translate([x, y, 0]) for x, y in corners])

    housing = rsq(ENG_L, 0)
    trans = hull(rsq(0.1, Z_T0 - 0.1), octa(0.1, BLOCK_R, z=Z_OCT))
    block = octa(BLOCK_L + 0.05, BLOCK_R, z=Z_OCT)
    ap = BLOCK_R * math.cos(math.radians(22.5))
    half_w = BLOCK_R * math.sin(math.radians(22.5))

    def skip(k, t, z, w, l):  # keep the stand socket area clean (face 4 = -x)
        return k == 4 and abs(z - Z_STAND) < 9 + l / 2 and abs(t) < 6 + w / 2

    gre = face_greebles(ap, half_w, Z_OCT + 2, Z_TOP - 2, 9, skip=skip)
    rings = [octa(1.6, BLOCK_R + 0.7, z=Z_OCT + 1.0), octa(1.6, BLOCK_R + 0.7, z=Z_TOP - 2.6)]
    m = union([housing, trans, block] + gre + rings)

    # engine housing detail: side grooves + one belt groove
    half = ENG_OFF + ENG_R
    cuts = []
    for a in range(4):
        cuts.append(rz(box(2.0, 1.4, ENG_L + 2, half, 0, ENG_L / 2), a * 90))
    belt = rsq(1.2, 14.0) - rsq(1.4, 13.9).scale([(half - 0.9) / half, (half - 0.9) / half, 1])
    cuts.append(belt)
    # interior
    cuts.append(octa(BLOCK_L, BLOCK_CAV_R, z=Z_FLOOR))
    for x, y in corners:
        z_led1 = BELL_D + 4.4
        cuts.append(cyl(BELL_D + 0.01, BELL_R, LED_D / 2, seg=64, z=-0.01).translate([x, y, 0]))  # bell
        cuts.append(cyl(5.0, LED_D / 2, seg=32, z=BELL_D - 0.2).translate([x, y, 0]))          # LED seat
        cuts.append(cyl(Z_FLOOR - z_led1 + 0.2, 3.25, seg=32, z=z_led1).translate([x, y, 0]))  # wire bore
    m -= union(cuts)

    # stand socket boss inside the cavity on the -x wall (underside sloped for printing)
    xin = -BLOCK_CAV_R * math.cos(math.radians(22.5)) - 0.5
    boss = hull(box(0.02, 14, 22.5, xin, 0, Z_STAND + 7 - 11.25),
                box(0.02, 14, 14, xin + 8.5, 0, Z_STAND))
    m += boss
    m -= cyl(14, 4.0 + CLEAR, seg=48).rotate([0, 90, 0]).translate([-BLOCK_R - 1.5, 0, Z_STAND])
    return m


def adapter():
    """Tapered collar between spine and block. Printed wide side down."""
    rl = BLOCK_CAV_R - 0.2
    lip = octa(4.1, rl)
    body = hull(octa(0.05, rl, z=4.0), octa(1.8, BLOCK_R, z=6.2), octa(0.05, SPINE_R + 0.5, z=29.95))
    plug = cyl(PLUG_L, PLUG_D / 2, seg=64, z=29.99)
    ribs = [rz(hull(box(1.4, 1.6, 0.1, BLOCK_R * 0.92 - 0.3, 0, 8.0), box(1.4, 1.6, 0.1, SPINE_R * 0.92 + 0.6, 0, 29.9)),
               k * 45) for k in range(8)]
    m = union([lip, body, plug] + ribs)
    m -= hull(octa(6.1, rl - 1.6, z=-0.1), octa(0.05, 3.0, z=27.0))
    m -= cyl(40, WIRE_D / 2, seg=32)
    return m


# ---------------------------------------------------------------------- stands
def stand_engine():
    ap = BLOCK_R * math.cos(math.radians(22.5))
    top = AXIS_H - ap
    base = cyl(4, 36, 34, seg=96)
    col = cyl(top - 3, 9, 6, seg=64, z=3.9)
    plug = cyl(9.0, 4.0, seg=48, z=top - 0.01)
    m = union([base, col, plug])
    m -= cyl(top + 12, 2.0, seg=24, z=-1)                 # cable channel
    m -= box(40, 4.0, 4.4, 20, 0, 0)                      # cable groove under base
    return m


def stand_front():
    base = cyl(4, 30, 28, seg=96)
    zc = AXIS_H - NECK_R - 4
    col = cyl(zc - 9, 7, 4.5, seg=64, z=3.9)
    cradle = hull(cyl(0.1, 4.5, seg=48, z=zc - 5.2), box(6, 22, 0.1, 0, 0, zc)) \
        + box(6, 22, 12, 0, 0, zc + 6)
    m = union([base, col, cradle])
    m -= cyl(10, NECK_R + 0.25, seg=64, z=-5).rotate([0, 90, 0]).translate([0, 0, AXIS_H])
    m -= box(8, 2 * NECK_R - 1.5, 12, 0, 0, AXIS_H + 6)   # open top of the U
    return m


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    front = crew_front()
    rear, neck_top = crew_rear()
    join = crew_joiner()
    seg1 = spine_segment(antenna_hole=True)
    seg2 = spine_segment()
    ant = antenna()
    adp = adapter()
    blk = engine_block()
    st_e = stand_engine()
    st_f = stand_front()

    for m, n in [(front, "01_crew_front.stl"), (rear, "02_crew_rear.stl"), (join, "03_crew_joiner_ring.stl"),
                 (seg1, "04_spine_segment_A_antenna.stl"), (seg2, "05_spine_segment_B.stl"),
                 (ant, "06_antenna_dish.stl"), (adp, "07_adapter_collar.stl"), (blk, "08_engine_block.stl"),
                 (st_e, "09_stand_engine.stl"), (st_f, "10_stand_front.stl")]:
        write_stl(m, n)

    # ---- assembled preview (ship axis = x, nose at x = 0, table at z = -AXIS_H)
    def fwd(m, c):   # print z -> ship -x
        return m.rotate([0, -90, 0]).translate([c, 0, 0])

    def aft(m, c):   # print z -> ship +x
        return m.rotate([0, 90, 0]).translate([c, 0, 0])

    x_mid = CREW_CYL + CREW_R
    x1 = x_mid + neck_top            # neck end = start of spine
    x2 = x1 + SEG_L
    x3 = x2 + SEG_L                  # end of spine
    x4 = x3 + 30.0 - 4.0             # block front face (adapter lip sits 4 mm inside)
    ap = SPINE_R * math.cos(math.radians(22.5))
    asm = [fwd(front, x_mid), aft(rear, x_mid), fwd(seg1, x2), fwd(seg2, x3),
           fwd(adp, x3 + 30.0), fwd(blk, x4 + Z_TOP),
           ant.translate([x2 - 12.0, 0, ap - 3.5]),
           st_e.translate([x4 + Z_TOP - Z_STAND, 0, -AXIS_H]),
           st_f.translate([x_mid + CREW_R + NECK_L / 2 + 1, 0, -AXIS_H])]
    full = Manifold.compose(asm)
    write_stl(full, "00_assembly_preview_only.stl")
    print(f"overall length: {x4 + Z_TOP:.0f} mm")


if __name__ == "__main__":
    main()
