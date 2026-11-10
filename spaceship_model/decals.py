#!/usr/bin/env python3
"""Decal sheet for the spaceship model: A4, scale 1:1, all sizes in millimetres.

Usage:  python3 decals.py      -> decals.svg  (convert to PDF/PNG with any browser, print at 100 %)
Change NAME / REGISTRY below to rename the ship.
"""
import math
import os

NAME = "PERIHELION"
REGISTRY = "DSV-27"
CLASS = "DEEP SPACE VESSEL"

INK = "#141414"
RED = "#c8102e"
YEL = "#ffcc00"
CUT = "#b8b8b8"
FONT = "DejaVu Sans, Liberation Sans, Arial, sans-serif"
MONO = "DejaVu Sans Mono, Liberation Mono, monospace"
out = []


def t(x, y, s, size, weight="bold", anchor="middle", fill=INK, sp=0.0, font=FONT, maxw=None):
    """Text; with maxw the size is reduced until the (estimated) width fits, and the width is then pinned."""
    extra = ""
    if maxw:
        n = len(s)
        per = 0.60 if font == MONO else (0.72 if weight == "bold" else 0.62)
        est = n * size * per + (n - 1) * sp
        if est > maxw:
            k = maxw / est
            size, sp = size * k, sp * k
            extra = f' textLength="{maxw:.2f}" lengthAdjust="spacingAndGlyphs"'
    out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{font}" font-size="{size:.2f}" font-weight="{weight}" '
               f'text-anchor="{anchor}" fill="{fill}" letter-spacing="{sp:.2f}"{extra}>{s}</text>')


def rect(x, y, w, h, fill="none", stroke="none", sw=0.2, rx=0.0):
    out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}" '
               f'stroke-width="{sw:.2f}" rx="{rx:.2f}"/>')


def cut(x, y, w, h):                       # hairline cutting frame
    rect(x, y, w, h, stroke=CUT, sw=0.08)


def line(x1, y1, x2, y2, sw=0.3, col=INK):
    out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{sw:.2f}"/>')


def poly(pts, fill=INK, stroke="none", sw=0.2):
    p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    out.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linejoin="round"/>')


def stripes(x, y, w, h, a=YEL, b=INK, pitch=2.0):
    """Diagonal hazard stripes."""
    cid = f"c{len(out)}"
    out.append(f'<clipPath id="{cid}"><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}"/></clipPath>')
    out.append(f'<g clip-path="url(#{cid})">')
    rect(x, y, w, h, fill=a)
    n = int((w + h) / pitch) + 2
    for i in range(0, n, 2):
        x0 = x + i * pitch - h
        poly([(x0, y + h), (x0 + pitch, y + h), (x0 + pitch + h, y), (x0 + h, y)], fill=b)
    out.append('</g>')


def arrow(x, y, length, ang=0.0, col=INK, w=1.0):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def P(u, v):
        return (x + u * c - v * s, y + u * s + v * c)
    hl = min(length * 0.45, 2.2 * w)
    poly([P(0, -w * 0.3), P(length - hl, -w * 0.3), P(length - hl, -w), P(length, 0),
          P(length - hl, w), P(length - hl, w * 0.3), P(0, w * 0.3)], fill=col)


def warn_triangle(cx, cy, size, symbol="!"):
    h = size * 0.866
    pts = [(cx, cy - h * 0.62), (cx + size / 2, cy + h * 0.38), (cx - size / 2, cy + h * 0.38)]
    poly(pts, fill=YEL, stroke=INK, sw=size * 0.07)
    if symbol == "!":
        t(cx, cy + size * 0.27, "!", size * 0.62)
    elif symbol == "bolt":
        poly([(cx + size * 0.05, cy - size * 0.22), (cx - size * 0.12, cy + size * 0.06), (cx - size * 0.01, cy + size * 0.06),
              (cx - size * 0.07, cy + size * 0.3), (cx + size * 0.13, cy - size * 0.02), (cx + size * 0.02, cy - size * 0.02)])


def trefoil(cx, cy, size):
    """Standard ionising-radiation warning symbol on a yellow field."""
    rect(cx - size / 2, cy - size / 2, size, size, fill=YEL, stroke=INK, sw=size * 0.05, rx=size * 0.08)
    r0, r1, rc = size * 0.09, size * 0.36, size * 0.055
    for k in range(3):
        a0, a1 = math.radians(k * 120 - 30 - 90), math.radians(k * 120 + 30 - 90)
        p = lambda r, a: (cx + r * math.cos(a), cy + r * math.sin(a))
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p(r0, a0), p(r1, a0), p(r1, a1), p(r0, a1)
        out.append(f'<path d="M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f} A{r1:.2f},{r1:.2f} 0 0 1 {x2:.2f},{y2:.2f} '
                   f'L{x3:.2f},{y3:.2f} A{r0:.2f},{r0:.2f} 0 0 0 {x0:.2f},{y0:.2f} Z" fill="{INK}"/>')
    out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{rc:.2f}" fill="{INK}"/>')


def plate(x, y, w, h, head, sub=None, col=INK, inv=False):
    """Stencil plate: framed label, optionally inverted (coloured field, white text)."""
    cut(x - 0.6, y - 0.6, w + 1.2, h + 1.2)
    if inv:
        rect(x, y, w, h, fill=col, rx=0.4)
        fg = "#ffffff"
    else:
        rect(x, y, w, h, stroke=col, sw=0.25, rx=0.4)
        fg = col
    if sub:
        t(x + w / 2, y + h * 0.47, head, h * 0.40, fill=fg, sp=0.12, maxw=w - 1.6)
        t(x + w / 2, y + h * 0.86, sub, h * 0.24, weight="normal", fill=fg, sp=0.05, maxw=w - 1.6)
    else:
        t(x + w / 2, y + h * 0.71, head, h * 0.56, fill=fg, sp=0.12, maxw=w - 1.4)


def name_block(x, y, w, h, small=False):
    cut(x, y, w, h)
    line(x + 1, y + h * 0.10, x + w - 1, y + h * 0.10, 0.35)
    rect(x + 1.2, y + h * 0.24, w * 0.035, h * 0.42, fill=RED)
    x0 = x + 1.2 + w * 0.035 + 1.2
    t((x0 + x + w - 1.2) / 2, y + h * 0.63, NAME, h * 0.50, sp=h * 0.05, maxw=x + w - 1.4 - x0)
    line(x + 1, y + h * 0.73, x + w - 1, y + h * 0.73, 0.35)
    t(x + w / 2, y + h * 0.92, f"{REGISTRY}  ·  {CLASS}", h * 0.14, weight="normal", sp=0.2, maxw=w - 3)


# ------------------------------------------------------------------ layout (A4)
W, H = 210.0, 297.0
t(10, 9, f"Decal-Bogen  {NAME} / {REGISTRY}   ·   Maßstab 1:1   ·   mit 100 % drucken (nicht „an Seite anpassen“)", 2.6, weight="normal", anchor="start")
line(150, 8, 200, 8, 0.25)
for k in range(6):
    line(150 + 10 * k, 6.8, 150 + 10 * k, 9.2, 0.25)
t(175, 6, "Kontrollmaß 50 mm", 2.2, weight="normal")

y = 14
t(10, y + 2.5, "A  Schiffsname, Reaktorblock links und rechts (Feld 64 × 16,5 mm)", 2.3, weight="normal", anchor="start")
name_block(10, y + 4, 60, 14.5)
name_block(76, y + 4, 60, 14.5)
cut(142, y + 4, 58, 14.5)
t(171, y + 13.2, REGISTRY, 9.0, sp=0.8, maxw=52)
line(144, y + 15.2, 198, y + 15.2, 0.6, RED)
t(171, y + 17.6, CLASS, 1.9, weight="normal", sp=0.5)

y = 38
t(10, y + 2.5, "B  Schiffsname, Kugel hinten links und rechts (Feld 30 × 9,6 mm)     C  Kennung groß", 2.3, weight="normal", anchor="start")
name_block(10, y + 4, 28, 8.4, small=True)
name_block(42, y + 4, 28, 8.4, small=True)
for i in range(3):
    cut(76 + i * 30, y + 4, 27, 8.4)
    t(89.5 + i * 30, y + 10.6, REGISTRY, 5.6, sp=0.5, maxw=24)
cut(168, y + 4, 32, 8.4)
t(184, y + 8.2, "CREW MODULE", 2.6, sp=0.3, maxw=29)
t(184, y + 11.2, "PRESSURISED · 101 kPa", 1.6, weight="normal", sp=0.15, maxw=29)

y = 56
t(10, y + 2.5, "D  Akkuwanne, Unterseite (Feld 83 × 19 mm)", 2.3, weight="normal", anchor="start")
cut(10, y + 4, 80, 17)
stripes(10.5, y + 4.5, 7, 16)
stripes(82.5, y + 4.5, 7, 16)
t(50, y + 11.0, "BATTERY ACCESS", 4.6, sp=0.5, maxw=60)
t(50, y + 14.6, "1  PULL LOCKING PIN     2  SWING DOWN     3  UNHOOK", 1.75, weight="normal", sp=0.12, maxw=60)
arrow(19.5, y + 18.5, 7, 0, RED, 0.8)
t(50, y + 19.1, "18650 Li-ION  3.7 V  ·  OBSERVE POLARITY", 1.75, sp=0.15, fill=RED, maxw=44)
arrow(80.5, y + 18.5, 7, 180, RED, 0.8)
t(96, y + 2.5, "E  Reaktor und Triebwerke", 2.3, weight="normal", anchor="start")
for i in range(3):
    trefoil(101 + i * 11, y + 9.5, 9)
    cut(96 + i * 11, y + 4.5, 10, 10)
for i in range(2):
    plate(131, y + 5 + i * 8.2, 32, 6.4, "CAUTION", "REACTOR SECTION · AUTHORISED CREW ONLY", RED, inv=(i == 0))
    plate(166, y + 5 + i * 8.2, 33, 6.4, "DANGER", "THRUSTER EXHAUST · KEEP CLEAR 50 m", RED, inv=(i == 0))
for i in range(3):
    warn_triangle(101 + i * 11, y + 18.0, 7.0, "!" if i < 2 else "bolt")
    cut(96 + i * 11, y + 14.9, 10, 6.6)

y = 82
t(10, y + 2.5, "F  Schleusen und Luken", 2.3, weight="normal", anchor="start")
for i in range(6):
    plate(10 + i * 21, y + 5, 18.5, 5.2, f"AIRLOCK {i + 1}", None, INK, inv=(i % 2 == 0))
for i in range(3):
    plate(137 + i * 21.5, y + 5, 19.5, 5.2, "EMERGENCY", "RELEASE · TURN LEFT", RED)
for i in range(6):
    cut(10 + i * 21, y + 12, 18.5, 5.4)
    arrow(11.2 + i * 21, y + 14.7, 6.0, 0, RED, 0.9)
    t(23.4 + i * 21, y + 15.6, "RESCUE", 2.3, fill=RED, sp=0.2, maxw=9.5)
for i in range(3):
    plate(137 + i * 21.5, y + 12.2, 19.5, 5.0, "HATCH", "OPENS OUTWARD", INK)

y = 103
t(10, y + 2.5, "G  Aufhängeösen, Trittverbote, Antenne", 2.3, weight="normal", anchor="start")
for i in range(3):
    cut(10 + i * 19, y + 4.5, 17, 8.5)
    poly([(18.5 + i * 19, y + 12.2), (15.5 + i * 19, y + 8.4), (21.5 + i * 19, y + 8.4)], fill=RED)
    t(18.5 + i * 19, y + 7.4, "HOIST POINT", 1.9, fill=RED, sp=0.12, maxw=15)
for i in range(6):
    plate(69 + i * 15.5, y + 5, 13.5, 3.6, "NO STEP", None, RED)
for i in range(6):
    plate(69 + i * 15.5, y + 10, 13.5, 3.6, "NO PUSH", None, INK)
plate(164, y + 5, 36, 8.6, "ANTENNA", "RF RADIATION · KEEP CLEAR WHEN ACTIVE", RED, inv=True)

y = 120
t(10, y + 2.5, "H  Tankmodule (Feld 12 × 7,5 mm): je ein Schild pro glattem Tankdeckel", 2.3, weight="normal", anchor="start")
media = ["PROPELLANT", "PROPELLANT", "COOLANT", "PROPELLANT", "N2", "H2O", "PROPELLANT", "O2", "COOLANT", "PROPELLANT", "PROPELLANT", "H2O"]
for i in range(12):
    x = 10 + i * 15.9
    cut(x, y + 4.5, 13.5, 7.0)
    rect(x + 0.6, y + 5.1, 12.3, 5.8, stroke=INK, sw=0.22, rx=0.3)
    t(x + 6.75, y + 8.5, f"T-{i + 1:02d}", 2.9, sp=0.2, maxw=10.5)
    t(x + 6.75, y + 10.3, media[i], 1.35, weight="normal", sp=0.1, maxw=10.5)

y = 135
t(10, y + 2.5, "I  Warnstreifen und Linien (beliebig zuschneiden)", 2.3, weight="normal", anchor="start")
for i in range(3):
    stripes(10, y + 5 + i * 4.2, 92, 2.6)
    cut(9.5, y + 4.5 + i * 4.2, 93, 3.6)
for i in range(3):
    stripes(108, y + 5 + i * 4.2, 92, 2.6, a="#ffffff", b=RED)
    cut(107.5, y + 4.5 + i * 4.2, 93, 3.6)
for i in range(4):
    rect(10, y + 18.5 + i * 2.6, 92, [1.6, 1.0, 0.6, 0.35][i], fill=RED)
    rect(108, y + 18.5 + i * 2.6, 92, [1.6, 1.0, 0.6, 0.35][i], fill=INK)

y = 166
t(10, y + 2.5, "J  Wartungsschilder, Typenschilder, Kleintext", 2.3, weight="normal", anchor="start")
texts = [("SERVICE PANEL", ["TORQUE 12 Nm", "INSPECT EVERY 400 h", "SEAL CLASS B"]),
         ("COOLANT LOOP 2", ["MAX 2.4 MPa", "ISOLATE BEFORE OPENING", "DRAIN VALVE BELOW"]),
         ("POWER BUS A", ["28 V DC · 40 A", "DISCONNECT BEFORE SERVICE", "FUSE PANEL F3"]),
         ("RCS CLUSTER", ["HYPERGOLIC", "PURGE LINE BEFORE WORK", "LEAK CHECK"]),
         ("EVA HANDHOLD", ["RATED 2 kN", "TETHER POINT", "CHECK LOCK"]),
         ("SENSOR BAY", ["OPTICS", "DO NOT TOUCH LENS", "COVER WHEN DOCKED"])]
for i, (head, lines_) in enumerate(texts):
    for j in range(2):
        x, yy = 10 + i * 32, y + 5 + j * 12.4
        cut(x, yy, 29.5, 11)
        rect(x + 0.6, yy + 0.6, 28.3, 9.8, stroke=INK, sw=0.2)
        rect(x + 0.6, yy + 0.6, 28.3, 3.0, fill=INK if j == 0 else RED)
        t(x + 14.75, yy + 2.85, head, 2.0, fill="#ffffff", sp=0.15, maxw=26)
        for k, ln in enumerate(lines_):
            t(x + 1.6, yy + 5.4 + k * 1.9, ln, 1.35, weight="normal", anchor="start", font=MONO, maxw=26)

y = 198
t(10, y + 2.5, "K  Ziffern, Pfeile, Kleinschilder (Reserve)", 2.3, weight="normal", anchor="start")
for j in range(2):
    for i in range(10):
        t(13 + i * 6.2, y + 10.5 + j * 7.5, str(i), 6.2, fill=INK if j == 0 else RED)
cut(10, y + 4.5, 63, 15.5)
for i in range(8):
    arrow(79 + (i % 4) * 13, y + 8 + (i // 4) * 7.5, 10, 0, RED if i < 4 else INK, 1.3)
cut(77, y + 4.5, 52, 15.5)
small = ["LIFT HERE", "VENT", "GROUND", "FILL PORT", "DRAIN", "O2", "N2", "H2O", "TEST", "PORT", "STBD", "ZENITH", "NADIR", "FWD", "AFT"]
for i, sm in enumerate(small):
    plate(133 + (i % 5) * 13.6, y + 5 + (i // 5) * 5.2, 12.2, 3.8, sm, None, INK if i % 2 else RED)

y = 223
t(10, y + 2.5, "L  Zweiter Satz der wichtigsten Schilder (Reserve, falls eines reißt)", 2.3, weight="normal", anchor="start")
name_block(10, y + 4, 60, 14.5)
name_block(76, y + 4, 28, 8.4, small=True)
cut(108, y + 4, 27, 8.4)
t(121.5, y + 10.6, REGISTRY, 5.6, sp=0.5, maxw=24)
trefoil(144, y + 9, 9)
cut(139, y + 4, 10, 10)
warn_triangle(157, y + 9.6, 8.0)
cut(152, y + 4.5, 10, 9)
plate(166, y + 5, 33, 6.4, "DANGER", "THRUSTER EXHAUST · KEEP CLEAR 50 m", RED, inv=True)
plate(76, y + 14.6, 18.5, 4.6, "AIRLOCK 1", None, INK, inv=True)
plate(97, y + 14.6, 18.5, 4.6, "AIRLOCK 2", None, INK)
plate(118, y + 14.6, 18.5, 4.6, "AIRLOCK 3", None, INK, inv=True)
for i in range(4):
    plate(140 + i * 15.2, y + 14.6, 13.5, 3.6, "NO STEP", None, RED)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
       f'<rect width="{W}" height="{H}" fill="#ffffff"/>' + "".join(out) + '</svg>')
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "decals.svg"), "w").write(svg)
print("decals.svg written:", len(out), "elements")
