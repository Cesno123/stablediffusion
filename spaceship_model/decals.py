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



def write_page(name):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>' + "".join(out) + '</svg>')
    here = os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(here, name), "w").write(svg)
    print(name, "written:", len(out), "elements")


write_page("decals.svg")

# =========================================================================== page 2
out = []
BLUE = "#0b4ea2"
GRN = "#1f8a3b"
ORG = "#f28c00"


def raw(s_):
    out.append(s_)


def picto(kind, col=INK):
    """Simple pictograms in a unit box (about -0.3 .. 0.3), drawn from scratch."""
    K = col
    if kind == "excl":
        return f'<rect x="-0.045" y="-0.27" width="0.09" height="0.34" rx="0.03" fill="{K}"/><circle cx="0" cy="0.2" r="0.055" fill="{K}"/>'
    if kind == "bolt":
        return f'<polygon points="0.06,-0.29 -0.14,0.04 -0.02,0.04 -0.08,0.3 0.14,-0.04 0.02,-0.04" fill="{K}"/>'
    if kind == "flame":
        return (f'<path d="M0,-0.3 C0.2,-0.1 0.24,0.06 0.17,0.2 C0.1,0.32 -0.1,0.32 -0.17,0.2 C-0.25,0.04 -0.08,-0.02 -0.06,-0.14 '
                f'C0,-0.06 0.05,-0.14 0,-0.3 Z" fill="{K}"/>')
    if kind == "cryo":
        o = ""
        for k in range(3):
            o += f'<g transform="rotate({60 * k})"><line x1="-0.28" y1="0" x2="0.28" y2="0" stroke="{K}" stroke-width="0.05"/>'
            for sx in (-1, 1):
                o += (f'<line x1="{0.17 * sx}" y1="0" x2="{0.25 * sx}" y2="-0.07" stroke="{K}" stroke-width="0.04"/>'
                      f'<line x1="{0.17 * sx}" y1="0" x2="{0.25 * sx}" y2="0.07" stroke="{K}" stroke-width="0.04"/>')
            o += '</g>'
        return o
    if kind == "laser":
        o = f'<circle cx="-0.05" cy="0" r="0.06" fill="{K}"/><line x1="-0.05" y1="0" x2="0.3" y2="0" stroke="{K}" stroke-width="0.045"/>'
        for k in range(12):
            a = math.radians(30 * k)
            r0, r1 = 0.1, (0.22 if k % 2 else 0.16)
            o += (f'<line x1="{-0.05 + r0 * math.cos(a):.3f}" y1="{r0 * math.sin(a):.3f}" x2="{-0.05 + r1 * math.cos(a):.3f}" '
                  f'y2="{r1 * math.sin(a):.3f}" stroke="{K}" stroke-width="0.03"/>')
        return o
    if kind == "magnet":
        return (f'<path d="M-0.2,-0.24 L-0.2,0.05 A0.2,0.2 0 0 0 0.2,0.05 L0.2,-0.24 L0.08,-0.24 L0.08,0.05 A0.08,0.08 0 0 1 -0.08,0.05 '
                f'L-0.08,-0.24 Z" fill="{K}"/><rect x="-0.21" y="-0.17" width="0.14" height="0.035" fill="#fff"/>'
                f'<rect x="0.07" y="-0.17" width="0.14" height="0.035" fill="#fff"/>')
    if kind == "hot":
        o = f'<rect x="-0.25" y="0.16" width="0.5" height="0.07" fill="{K}"/>'
        for x in (-0.15, 0.0, 0.15):
            o += (f'<path d="M{x},0.09 q0.07,-0.08 0,-0.16 q-0.07,-0.08 0,-0.16" fill="none" stroke="{K}" stroke-width="0.045" '
                  f'stroke-linecap="round"/>')
        return o
    if kind == "rot":
        return (f'<path d="M0.2,0.06 A0.21,0.21 0 1 1 0.06,-0.2" fill="none" stroke="{K}" stroke-width="0.06"/>'
                f'<polygon points="0.02,-0.31 0.2,-0.2 0.03,-0.08" fill="{K}"/><circle cx="0" cy="0" r="0.05" fill="{K}"/>')
    if kind == "gauge":
        o = f'<circle cx="0" cy="0.02" r="0.23" fill="none" stroke="{K}" stroke-width="0.05"/><line x1="0" y1="0.02" x2="0.12" y2="-0.12" stroke="{K}" stroke-width="0.05" stroke-linecap="round"/><circle cx="0" cy="0.02" r="0.04" fill="{K}"/>'
        for k in range(5):
            a = math.radians(200 + 35 * k)
            o += (f'<line x1="{0.16 * math.cos(a):.3f}" y1="{0.02 + 0.16 * math.sin(a):.3f}" x2="{0.2 * math.cos(a):.3f}" '
                  f'y2="{0.02 + 0.2 * math.sin(a):.3f}" stroke="{K}" stroke-width="0.03"/>')
        return o
    if kind == "pinch":
        return (f'<rect x="-0.025" y="-0.26" width="0.05" height="0.52" fill="{K}"/>'
                f'<polygon points="-0.3,-0.04 -0.16,-0.04 -0.16,-0.12 -0.05,0 -0.16,0.12 -0.16,0.04 -0.3,0.04" fill="{K}"/>'
                f'<polygon points="0.3,-0.04 0.16,-0.04 0.16,-0.12 0.05,0 0.16,0.12 0.16,0.04 0.3,0.04" fill="{K}"/>')
    if kind == "boom":
        pts = []
        for k in range(16):
            a = math.radians(22.5 * k - 90)
            r = 0.3 if k % 2 == 0 else 0.13
            pts.append(f"{r * math.cos(a):.3f},{r * math.sin(a):.3f}")
        return f'<polygon points="{" ".join(pts)}" fill="{K}"/>'
    if kind == "tref":
        o = f'<circle cx="0" cy="0" r="0.045" fill="{K}"/>'
        for k in range(3):
            a0, a1 = math.radians(k * 120 - 120), math.radians(k * 120 - 60)
            r0, r1 = 0.085, 0.28
            o += (f'<path d="M{r0 * math.cos(a0):.3f},{r0 * math.sin(a0):.3f} L{r1 * math.cos(a0):.3f},{r1 * math.sin(a0):.3f} '
                  f'A{r1},{r1} 0 0 1 {r1 * math.cos(a1):.3f},{r1 * math.sin(a1):.3f} L{r0 * math.cos(a1):.3f},{r0 * math.sin(a1):.3f} '
                  f'A{r0},{r0} 0 0 0 {r0 * math.cos(a0):.3f},{r0 * math.sin(a0):.3f} Z" fill="{K}"/>')
        return o
    if kind == "drop":
        return f'<path d="M0,-0.3 C0.14,-0.08 0.2,0.04 0.2,0.12 A0.2,0.2 0 0 1 -0.2,0.12 C-0.2,0.04 -0.14,-0.08 0,-0.3 Z" fill="{K}"/>'
    if kind == "hand":
        return (f'<rect x="-0.13" y="-0.02" width="0.26" height="0.26" rx="0.06" fill="{K}"/>'
                + "".join(f'<rect x="{-0.13 + 0.07 * i:.3f}" y="{-0.26 + (0.04 if i in (0, 3) else 0):.3f}" width="0.05" height="0.3" rx="0.025" fill="{K}"/>' for i in range(4))
                + f'<rect x="0.13" y="0.02" width="0.05" height="0.16" rx="0.025" fill="{K}" transform="rotate(-25 0.13 0.1)"/>')
    fs = 0.46 if len(kind) <= 2 else 0.26
    return f'<text x="0" y="{fs * 0.36:.2f}" font-family="{FONT}" font-size="{fs}" font-weight="bold" text-anchor="middle" fill="{K}">{kind}</text>'


def place(cx, cy, scale, inner):
    raw(f'<g transform="translate({cx:.2f},{cy:.2f}) scale({scale:.3f})">{inner}</g>')


def tri(cx, cy, size, kind, fill=YEL, border=INK, fg=INK, inv=False, frame=True):
    """Triangular sign, point up (warning) or point down (marker)."""
    h = size * 0.866
    if inv:
        pts = [(cx, cy + h * 0.62), (cx + size / 2, cy - h * 0.38), (cx - size / 2, cy - h * 0.38)]
        oy = -size * 0.10
    else:
        pts = [(cx, cy - h * 0.62), (cx + size / 2, cy + h * 0.38), (cx - size / 2, cy + h * 0.38)]
        oy = size * 0.09
    poly(pts, fill=fill, stroke=border, sw=size * 0.07)
    place(cx, cy + oy, size * 0.62, picto(kind, fg))
    if frame:
        cut(cx - size / 2 - 0.9, cy - h * 0.62 - 0.9, size + 1.8, h + 1.8)


def ring_sign(cx, cy, d, kind, mode="no"):
    """Round signs: 'no' = prohibition (red ring + slash), 'do' = mandatory (blue disc)."""
    cut(cx - d / 2 - 0.7, cy - d / 2 - 0.7, d + 1.4, d + 1.4)
    if mode == "no":
        raw(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{d * 0.44:.2f}" fill="#fff" stroke="{RED}" stroke-width="{d * 0.1:.2f}"/>')
        k = d * 0.31
        if kind.isupper():
            line(cx - k, cy - k, cx + k, cy + k, d * 0.09, RED)
            place(cx, cy, d * 0.62, picto(kind, INK))
        else:
            place(cx, cy, d * 0.62, picto(kind, INK))
            line(cx - k, cy - k, cx + k, cy + k, d * 0.09, RED)
    else:
        raw(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{d * 0.48:.2f}" fill="{BLUE}"/>')
        place(cx, cy, d * 0.62, picto(kind, "#ffffff"))


def diamond(cx, cy, size, label, fill, fg=INK, top=None):
    r = size / 2
    poly([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill, stroke=INK, sw=size * 0.05)
    if top:
        place(cx, cy - r * 0.42, size * 0.42, picto(top, fg))
    t(cx, cy + r * (0.42 if top else 0.16), label, size * 0.26, fill=fg, maxw=size * 0.5)
    cut(cx - r - 0.7, cy - r - 0.7, size + 1.4, size + 1.4)


def target(cx, cy, d):
    cut(cx - d / 2 - 0.7, cy - d / 2 - 0.7, d + 1.4, d + 1.4)
    for k, f in enumerate((0.48, 0.34, 0.2)):
        raw(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{d * f:.2f}" fill="none" stroke="{INK if k != 1 else RED}" stroke-width="{d * 0.035:.2f}"/>')
    line(cx - d * 0.48, cy, cx + d * 0.48, cy, d * 0.025)
    line(cx, cy - d * 0.48, cx, cy + d * 0.48, d * 0.025)
    raw(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{d * 0.05:.2f}" fill="{RED}"/>')


def emblem(cx, cy, size, frame=True):
    """Original ship emblem: delta with a small sun at the focus of a tilted orbit (perihelion)."""
    h = size * 0.866
    pts = [(cx, cy - h * 0.62), (cx + size / 2, cy + h * 0.38), (cx - size / 2, cy + h * 0.38)]
    poly(pts, fill="#ffffff", stroke=INK, sw=size * 0.06)
    ox, oy = cx + size * 0.03, cy + size * 0.07
    raw(f'<g transform="rotate(-32 {ox:.2f} {oy:.2f})">'
        f'<ellipse cx="{ox:.2f}" cy="{oy:.2f}" rx="{size * 0.25:.2f}" ry="{size * 0.085:.2f}" fill="none" stroke="{INK}" stroke-width="{size * 0.022:.2f}"/>'
        f'<circle cx="{ox - size * 0.17:.2f}" cy="{oy:.2f}" r="{size * 0.045:.2f}" fill="{RED}"/>'
        f'<circle cx="{ox + size * 0.25:.2f}" cy="{oy:.2f}" r="{size * 0.032:.2f}" fill="{INK}"/></g>')
    line(cx - size * 0.2, cy + h * 0.25, cx + size * 0.2, cy + h * 0.25, size * 0.02)
    if frame:
        cut(cx - size / 2 - 0.9, cy - h * 0.62 - 0.9, size + 1.8, h + 1.8)


def badge(cx, cy, d):
    """Round mission badge with the ship name running around the rim."""
    pid = f"p{len(out)}"
    r = d / 2
    cut(cx - r - 0.7, cy - r - 0.7, d + 1.4, d + 1.4)
    raw(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{INK}"/><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * 0.7:.2f}" fill="#ffffff"/>')
    raw(f'<path id="{pid}" d="M{cx - r * 0.79:.2f},{cy:.2f} A{r * 0.79:.2f},{r * 0.79:.2f} 0 1 1 {cx + r * 0.79:.2f},{cy:.2f} '
        f'A{r * 0.79:.2f},{r * 0.79:.2f} 0 1 1 {cx - r * 0.79:.2f},{cy:.2f}" fill="none"/>')
    txt = f"{NAME} · {REGISTRY} · {CLASS} · "
    raw(f'<text font-family="{FONT}" font-size="{r * 0.17:.2f}" font-weight="bold" fill="#ffffff" letter-spacing="{r * 0.012:.2f}">'
        f'<textPath href="#{pid}" textLength="{2 * math.pi * r * 0.79 * 0.985:.2f}" lengthAdjust="spacing">{txt}</textPath></text>')
    emblem(cx, cy + r * 0.04, r * 1.0, frame=False)


def hexa(cx, cy, size, label, col=INK):
    pts = [(cx + size / 2 * math.cos(math.radians(60 * k)), cy + size / 2 * math.sin(math.radians(60 * k))) for k in range(6)]
    poly(pts, fill="#ffffff", stroke=col, sw=size * 0.06)
    t(cx, cy + size * 0.1, label, size * 0.26, fill=col, maxw=size * 0.72)
    cut(cx - size / 2 - 0.6, cy - size * 0.433 - 0.6, size + 1.2, size * 0.866 + 1.2)


def chevrons(x, y, w, h, col, pitch=None):
    pitch = pitch or h * 1.1
    cid = f"c{len(out)}"
    raw(f'<clipPath id="{cid}"><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}"/></clipPath><g clip-path="url(#{cid})">')
    n = int(w / pitch) + 3
    for i in range(0, n, 2):
        x0 = x + i * pitch - h
        poly([(x0, y), (x0 + pitch, y), (x0 + pitch + h / 2, y + h / 2), (x0 + pitch, y + h), (x0, y + h), (x0 + h / 2, y + h / 2)], fill=col)
    raw('</g>')
    cut(x - 0.5, y - 0.5, w + 1, h + 1)


def pennant(x, y, w, h, label, col):
    poly([(x, y), (x + w, y + h / 2), (x, y + h)], fill=col)
    t(x + w * 0.30, y + h * 0.62, label, h * 0.34, fill="#ffffff", maxw=w * 0.46)
    cut(x - 0.6, y - 0.6, w + 1.2, h + 1.2)


def curved(cx, cy, r, label, col, ccw=False):
    a0, a1 = (200, -20) if not ccw else (-20, 200)
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    (x0, y0), (x1, y1) = p(200), p(-20)
    raw(f'<path d="M{x0:.2f},{y0:.2f} A{r:.2f},{r:.2f} 0 1 1 {x1:.2f},{y1:.2f}" fill="none" stroke="{col}" stroke-width="{r * 0.22:.2f}"/>')
    ex, ey = (x1, y1) if not ccw else (x0, y0)
    d = 1 if not ccw else -1
    poly([(ex - r * 0.3, ey - r * 0.02), (ex + r * 0.3, ey - r * 0.02), (ex + d * 0.0, ey + r * 0.42)], fill=col)
    t(cx, cy + r * 0.2, label, r * 0.42, fill=col, maxw=r * 1.25)
    cut(cx - r * 1.35, cy - r * 1.25, r * 2.7, r * 2.6)


t(10, 9, f"Decal-Bogen 2  {NAME} / {REGISTRY}   ·   Maßstab 1:1   ·   mit 100 % drucken", 2.6, weight="normal", anchor="start")
line(150, 8, 200, 8, 0.25)
for k in range(6):
    line(150 + 10 * k, 6.8, 150 + 10 * k, 9.2, 0.25)
t(175, 6, "Kontrollmaß 50 mm", 2.2, weight="normal")

kinds = ["excl", "bolt", "flame", "cryo", "laser", "magnet", "hot", "rot", "gauge", "pinch", "boom", "tref", "drop"]
y = 14
t(10, y + 2.5, "M  Warndreiecke in drei Größen (10 / 7,5 / 5 mm): Allgemein, Spannung, Feuer, Kälte, Laser, Magnetfeld, heiß, rotierend, Druck, Quetschen, Explosion, Strahlung, Flüssigkeit", 2.1, weight="normal", anchor="start")
for i, k in enumerate(kinds):
    tri(17 + i * 14.4, y + 10.5, 10.0, k)
    tri(17 + i * 14.4, y + 21.5, 7.5, k)
for i in range(26):
    tri(13.5 + i * 7.2, y + 30.0, 5.0, kinds[i % 13])

y = 50
t(10, y + 2.5, "N  Dreiecksmarken, Spitze nach unten: zeigen auf die gemeinte Stelle (11 mm, rot gefüllt und rot umrandet)", 2.1, weight="normal", anchor="start")
labels = ["CUT", "JACK", "LIFT", "EXIT", "O2", "FUEL", "VENT", "TOW", "N2", "H2O", "GND", "TEST", "FILL"]
for i, lb in enumerate(labels):
    tri(17 + i * 14.4, y + 9.5, 11.0, lb, fill=RED, border=RED, fg="#ffffff", inv=True)
    tri(17 + i * 14.4, y + 21.0, 11.0, lb, fill="#ffffff", border=RED, fg=RED, inv=True)

y = 78
t(10, y + 2.5, "O  Verbotszeichen (rot) und Gebotszeichen (blau), 10 mm", 2.1, weight="normal", anchor="start")
for i, k in enumerate(["flame", "hand", "bolt", "magnet", "STEP", "PUSH", "laser", "drop"]):
    ring_sign(16 + i * 12.6, y + 10, 10, k, "no")
for i, k in enumerate(["TETHER", "VISOR", "GND", "LOCK", "SEAL", "CHECK", "PURGE"]):
    ring_sign(120 + i * 12.6, y + 10, 10, k, "do")

y = 96
t(10, y + 2.5, "P  Gefahrstoff-Rauten für Tanks und Leitungen, 12 mm", 2.1, weight="normal", anchor="start")
dia = [("LH2", RED, "#fff", "flame"), ("LOX", YEL, INK, "drop"), ("N2H4", ORG, INK, "boom"), ("He", GRN, "#fff", "gauge"), ("N2", GRN, "#fff", "gauge"),
       ("H2O", BLUE, "#fff", "drop"), ("NH3", "#ffffff", INK, "excl"), ("Xe", "#ffffff", INK, "gauge"), ("CRYO", BLUE, "#fff", "cryo"),
       ("HV", YEL, INK, "bolt"), ("RAD", YEL, INK, "tref"), ("HOT", ORG, INK, "hot"), ("LASER", YEL, INK, "laser")]
for i, (lb, f, fg, top) in enumerate(dia):
    diamond(17 + i * 14.4, y + 11.5, 12, lb, f, fg, top)

y = 117
t(10, y + 2.5, "Q  Andockziele und Passmarken", 2.1, weight="normal", anchor="start")
x = 18
for d in (16, 16, 13, 13, 10, 10, 8, 8):
    target(x, y + 12.5, d)
    x += d + 4
for i in range(8):
    cxm, cym = 143 + (i % 4) * 8.2, y + 8 + (i // 4) * 8.5
    line(cxm - 3, cym, cxm + 3, cym, 0.3, RED if i % 2 else INK)
    line(cxm, cym - 3, cxm, cym + 3, 0.3, RED if i % 2 else INK)
    raw(f'<circle cx="{cxm:.2f}" cy="{cym:.2f}" r="1.6" fill="none" stroke="{RED if i % 2 else INK}" stroke-width="0.3"/>')
    cut(cxm - 3.8, cym - 3.8, 7.6, 7.6)
for i in range(4):
    cxm, cym = 181 + (i % 2) * 13, y + 7 + (i // 2) * 9
    for sx in (-1, 1):
        for sy in (-1, 1):
            line(cxm + sx * 5, cym + sy * 3, cxm + sx * 5, cym + sy * 1.4, 0.4)
            line(cxm + sx * 5, cym + sy * 3, cxm + sx * 3.2, cym + sy * 3, 0.4)
    t(cxm, cym + 0.9, f"P-{i + 1}", 2.4, maxw=7)
    cut(cxm - 6, cym - 4, 12, 8)

y = 140
t(10, y + 2.5, "R  Schiffsabzeichen: rundes Missionsabzeichen und dreieckiges Emblem", 2.1, weight="normal", anchor="start")
badge(24, y + 18, 26)
badge(54, y + 18, 26)
badge(79.5, y + 13.5, 17)
badge(79.5, y + 31.0, 13)
badge(98, y + 13.5, 17)
badge(98, y + 31.0, 13)
for xe, sz in ((126, 22), (150.5, 22), (172.5, 15), (190.5, 15)):
    emblem(xe, y + (16.5 if sz > 20 else 13.5), sz)
for i in range(8):
    emblem(114 + i * 11.2, y + 33, 8.5)

y = 181
t(10, y + 2.5, "S  Sektions- und Feldmarken: Dreiecke 1–10, Sechsecke, Feldnummern", 2.1, weight="normal", anchor="start")
for i in range(10):
    tri(15.5 + i * 11.2, y + 10, 9.0, str(i + 1), fill="#ffffff", border=INK if i % 2 else RED, fg=INK if i % 2 else RED)
for i, lb in enumerate(["RCS 1", "RCS 2", "RCS 3", "RCS 4", "CAM 1", "CAM 2", "ANT", "DOCK"]):
    hexa(126 + i * 10.2, y + 9.2, 9.4, lb, INK if i % 2 else BLUE)
for i in range(20):
    row, col_ = i // 10, i % 10
    plate(10 + col_ * 19.2, y + 17 + row * 5.4, 17.2, 3.8, f"{'ABCD'[i % 4]}-{i + 1:02d}", None, INK if (i + row) % 2 else RED, inv=(i % 5 == 0))

y = 211
t(10, y + 2.5, "T  Richtungsbänder, Schachbrett, Skalen (beliebig zuschneiden)", 2.1, weight="normal", anchor="start")
chevrons(10, y + 5, 92, 3.2, RED)
chevrons(108, y + 5, 92, 3.2, INK)
chevrons(10, y + 10, 92, 2.2, ORG)
chevrons(108, y + 10, 92, 2.2, BLUE)
for j in range(2):
    xs = 10 + j * 98
    for i in range(46):
        for r_ in range(2):
            if (i + r_) % 2 == 0:
                rect(xs + i * 2.0, y + 14.2 + r_ * 1.5, 2.0, 1.5, fill=INK if j == 0 else RED)
    cut(xs - 0.5, y + 13.7, 93, 4)
for j in range(2):
    xs = 10 + j * 98
    line(xs, y + 22.5, xs + 92, y + 22.5, 0.25)
    for i in range(93):
        hh = 2.2 if i % 10 == 0 else (1.5 if i % 5 == 0 else 0.9)
        line(xs + i, y + 22.5, xs + i, y + 22.5 - hh, 0.18)
        if i % 10 == 0 and i < 90:
            t(xs + i + 0.5, y + 19.6, str(i // 10 * (10 if j == 0 else 1)), 1.5, weight="normal", anchor="start")
    cut(xs - 0.5, y + 18.2, 93, 5)

y = 238
t(10, y + 2.5, "U  Drehpfeile, Wimpel, kleine Dreiecke als Zierde", 2.1, weight="normal", anchor="start")
for i, (lb, col_, ccw) in enumerate([("OPEN", RED, False), ("LOCK", INK, True), ("OPEN", INK, False), ("LOCK", RED, True), ("VENT", BLUE, False), ("SEAL", BLUE, True)]):
    curved(17 + i * 13.5, y + 11.5, 4.6, lb, col_, ccw)
for i, (lb, col_) in enumerate([("FWD", RED), ("AFT", INK), ("PORT", RED), ("STBD", GRN), ("ZENITH", BLUE), ("NADIR", INK)]):
    pennant(93 + (i % 3) * 20, y + 5 + (i // 3) * 7.6, 17.5, 6.0, lb, col_)
cols = [INK, RED, YEL, BLUE, ORG]
for r_ in range(3):
    for i in range(11):
        sz = [4.2, 3.2, 2.4][r_]
        cx_, cy_ = 156 + i * 4.2, y + 7.5 + r_ * 5.4
        h_ = sz * 0.866
        up = (i + r_) % 2 == 0
        pts = [(cx_, cy_ - h_ / 2), (cx_ + sz / 2, cy_ + h_ / 2), (cx_ - sz / 2, cy_ + h_ / 2)] if up else \
              [(cx_, cy_ + h_ / 2), (cx_ + sz / 2, cy_ - h_ / 2), (cx_ - sz / 2, cy_ - h_ / 2)]
        poly(pts, fill=cols[(i + r_) % 5] if i % 3 else "#ffffff", stroke=cols[(i + r_) % 5], sw=0.3)
cut(153, y + 4.5, 47.5, 17)

y = 264
t(10, y + 2.5, "V  Seriennummern und Strichcodes", 2.1, weight="normal", anchor="start")
import random as _r
_r.seed(27)
for i in range(6):
    x = 10 + i * 32
    cut(x, y + 4.5, 29.5, 9.5)
    xx = x + 1.2
    while xx < x + 28:
        wbar = _r.choice([0.25, 0.25, 0.4, 0.6])
        rect(xx, y + 5.3, wbar, 5.2, fill=INK)
        xx += wbar + _r.choice([0.25, 0.3, 0.5])
    t(x + 14.75, y + 13.0, f"{REGISTRY}-{'ABCDEF'[i]}{_r.randint(1000, 9999)}-{_r.randint(10, 99)}", 1.6, weight="normal", font=MONO, maxw=27)

write_page("decals_2.svg")
