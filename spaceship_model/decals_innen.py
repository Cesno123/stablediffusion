#!/usr/bin/env python3
"""Decal sheet for the bridge insert (part 04) of the 100 cm model: A4, scale 1:1, sizes in mm.

Usage:  python3 decals_innen.py  -> decals_innen.svg  (print at 100 %, no "fit to page")
Every decal is 0.3 mm smaller than the recess it goes into. Each set is on the sheet twice (spares).
"""
import math
import random

rng = random.Random(27)
BG = "#0a1420"
CY, AM, GR, RD, WH, VI = "#3fd2ff", "#ffb300", "#58f08c", "#ff5148", "#eaf4ff", "#b48cff"
INK = "#141414"
CUT = "#9a9a9a"
FONT = "DejaVu Sans, Liberation Sans, Arial, sans-serif"
out = []


def R(x, y, w, h, fill, rx=0.0, stroke="none", sw=0.1):
    out.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{rx:.3f}" fill="{fill}" '
               f'stroke="{stroke}" stroke-width="{sw:.3f}"/>')


def L(x1, y1, x2, y2, col, sw=0.12):
    out.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{col}" stroke-width="{sw:.3f}" '
               f'stroke-linecap="round"/>')


def C(cx, cy, r, fill="none", stroke="none", sw=0.12):
    out.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.3f}"/>')


def P(pts, col, sw=0.12, fill="none"):
    p = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
    out.append(f'<polyline points="{p}" fill="{fill}" stroke="{col}" stroke-width="{sw:.3f}" stroke-linejoin="round" '
               f'stroke-linecap="round"/>')


def T(x, y, s, size, col=INK, anchor="start", weight="normal"):
    out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size:.2f}" font-weight="{weight}" '
               f'text-anchor="{anchor}" fill="{col}">{s}</text>')


# ------------------------------------------------------------------ screen contents
def k_bars(x, y, w, h):
    n = max(3, int(w / 0.45))
    bw = w / n
    for i in range(n):
        v = rng.uniform(0.2, 1.0)
        R(x + i * bw + bw * 0.15, y + h * (1 - v), bw * 0.7, h * v, rng.choice([CY, CY, AM, GR]))


def k_wave(x, y, w, h):
    for col, ph in ((CY, 0.0), (AM, 1.7)):
        f = rng.uniform(1.5, 3.5)
        P([(x + w * i / 40, y + h / 2 + h * 0.4 * math.sin(ph + f * 2 * math.pi * i / 40) * (0.5 + 0.5 * i / 40))
           for i in range(41)], col, 0.13)
    L(x, y + h / 2, x + w, y + h / 2, WH, 0.05)


def k_orbit(x, y, w, h):
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    for f in (0.35, 0.65, 0.95):
        C(cx, cy, r * f, stroke=CY, sw=0.08)
    C(cx, cy, r * 0.12, fill=AM)
    for f in (0.35, 0.65, 0.95):
        a = rng.uniform(0, 6.28)
        C(cx + r * f * math.cos(a), cy + r * f * math.sin(a), max(0.14, r * 0.07), fill=rng.choice([WH, GR, RD]))
    L(cx - r, cy, cx + r, cy, CY, 0.05)
    L(cx, cy - r, cx, cy + r, CY, 0.05)


def k_map(x, y, w, h):
    for i in range(1, 4):
        L(x + w * i / 4, y, x + w * i / 4, y + h, CY, 0.04)
        L(x, y + h * i / 4, x + w, y + h * i / 4, CY, 0.04)
    pts = [(x + rng.uniform(0.08, 0.92) * w, y + rng.uniform(0.08, 0.92) * h) for _ in range(9)]
    for px, py in pts:
        C(px, py, rng.choice([0.1, 0.14, 0.2]), fill=rng.choice([WH, WH, AM, CY]))
    P(sorted(pts[:5]), AM, 0.1)
    C(pts[0][0], pts[0][1], 0.42, stroke=RD, sw=0.09)


def k_ship(x, y, w, h):
    """Side view of the ship (sphere, spine, engine block) with status dots."""
    vert = h > w
    def q(u, v):                           # u along the ship 0..1, v across -1..1
        return (x + w / 2 + v * w * 0.22, y + h * (0.06 + 0.88 * u)) if vert else (x + w * (0.05 + 0.9 * u), y + h / 2 + v * h * 0.3)
    s = (h if vert else w)
    c = q(0.09, 0)
    C(c[0], c[1], s * 0.085, stroke=CY, sw=0.12)
    a, b = q(0.18, 0), q(0.78, 0)
    L(a[0], a[1], b[0], b[1], CY, 0.22)
    for u in (0.3, 0.42, 0.54, 0.66):
        p1, p2 = q(u, -0.35), q(u, 0.35)
        L(p1[0], p1[1], p2[0], p2[1], CY, 0.1)
    p = [q(0.78, -0.6), q(0.95, -0.6), q(0.95, 0.6), q(0.78, 0.6), q(0.78, -0.6)]
    P(p, CY, 0.12)
    for u, v, col in ((0.09, 0, GR), (0.48, 0, GR), (0.86, 0, AM), (0.95, -0.35, RD), (0.95, 0.35, GR)):
        d = q(u, v)
        C(d[0], d[1], 0.17, fill=col)


def k_text(x, y, w, h):
    n = max(2, int(h / 0.42))
    for i in range(n):
        yy = y + h * (i + 0.5) / n
        L(x, yy, x + w * rng.uniform(0.35, 1.0), yy, rng.choice([CY, CY, WH, AM]), min(0.16, h / n * 0.45))


def k_keys(x, y, w, h):
    nx = max(2, int(w / 0.55))
    ny = max(1, int(h / 0.55))
    for i in range(nx):
        for j in range(ny):
            R(x + w * i / nx + 0.05, y + h * j / ny + 0.05, w / nx - 0.1, h / ny - 0.1,
              rng.choice([CY, CY, AM, GR, RD, VI, WH]), rx=0.06)


def k_gauge(x, y, w, h):
    n = max(1, int(w / max(h, 0.8)))
    for i in range(n):
        cx, cy, r = x + w * (i + 0.5) / n, y + h * 0.5, min(w / n, h) * 0.42
        C(cx, cy, r, stroke=CY, sw=0.1)
        a = rng.uniform(-2.6, -0.5)
        L(cx, cy, cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a), rng.choice([AM, RD, GR]), 0.12)


def k_split(x, y, w, h):
    kinds = [k_bars, k_wave, k_text, k_gauge, k_orbit, k_map]
    if h >= w:
        rng.choice(kinds)(x, y, w, h * 0.52)
        rng.choice([k_text, k_bars, k_keys])(x, y + h * 0.6, w, h * 0.4)
    else:
        rng.choice(kinds)(x, y, w * 0.55, h)
        rng.choice([k_text, k_keys])(x + w * 0.62, y, w * 0.38, h)


def screen(x, y, w, h, kind, head=None):
    """One decal: dark screen with a thin light frame; x, y = top left."""
    R(x, y, w, h, BG, rx=min(0.35, h * 0.2))
    m = 0.22 if min(w, h) > 2 else 0.14
    R(x + m / 2, y + m / 2, w - m, h - m, "none", rx=min(0.3, h * 0.18), stroke=head or CY, sw=0.06)
    kind(x + m + 0.12, y + m + 0.12, w - 2 * m - 0.24, h - 2 * m - 0.24)


def door(x, y, w, h, num):
    R(x, y, w, h, "#c9ced6", rx=0.3)
    R(x + 0.25, y + 0.25, w - 0.5, h - 0.5, "none", rx=0.2, stroke="#6b7480", sw=0.1)
    L(x + w / 2, y + 0.3, x + w / 2, y + h - 0.3, "#3a4048", 0.14)
    R(x + 0.5, y + h * 0.28, w - 1.0, 1.1, "#c8102e")
    R(x + 0.5, y + h * 0.28 + 1.3, w - 1.0, 0.3, "#c8102e")
    T(x + w / 2, y + h * 0.28 + 0.88, f"LIFT {num}", 0.85, WH, "middle", "bold")
    for sx in (0.27, 0.73):                                  # door windows
        R(x + w * sx - 0.6, y + h * 0.1, 1.2, 1.9, BG, rx=0.3)
    for i in range(5):                                       # hazard strip at the bottom
        R(x + 0.5 + i * (w - 1.0) / 5, y + h - 1.3, (w - 1.0) / 10, 0.8, "#ffcc00")
        R(x + 0.5 + (i + 0.5) * (w - 1.0) / 5, y + h - 1.3, (w - 1.0) / 10, 0.8, INK)


def sign(x, y, w, h, text, fill, fg=WH):
    R(x, y, w, h, fill, rx=0.2)
    out.append(f'<text x="{x + w / 2:.2f}" y="{y + h * 0.70:.2f}" font-family="{FONT}" font-size="{h * 0.55:.2f}" '
               f'font-weight="bold" text-anchor="middle" fill="{fg}" textLength="{w - 1.2:.2f}" '
               f'lengthAdjust="spacingAndGlyphs">{text}</text>')


# ------------------------------------------------------------------ sheet
W, H = 210.0, 297.0
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">')
R(0, 0, W, H, "#ffffff")
T(12, 14, "PERIHELION · Decals Brücke (Teil 04) · Modell 100 cm · Maßstab 1:1 · mit 100 % drucken", 3.6, INK, weight="bold")
T(12, 19, "Jeder Satz ist zweimal vorhanden (Reserve). Maße in mm. Buchstaben = Einbauort, siehe Plan unten.", 2.8, "#444")

GAP = 1.6
y = 27.0


def row(letter, title, w, h, n, kinds, special=None):
    """One labelled row holding two sets of n decals."""
    global y
    T(12, y + 3.0, letter, 5.0, "#c8102e", weight="bold")
    T(19, y + 1.6, title, 2.6, INK, weight="bold")
    T(19, y + 4.6, f"{n} Stück · {w:.1f} × {h:.1f} mm", 2.3, "#555")
    x = 70.0
    for s in range(2):
        for i in range(n):
            if x + w > W - 10:
                x = 70.0
                y += h + GAP
            if special:
                special(x, y, w, h, i)
            else:
                screen(x, y, w, h, kinds[i % len(kinds)], head=[CY, AM, CY, GR][i % 4])
            x += w + GAP
        x += 3.0
    y += max(h, 6.0) + 4.0


row("A", "Hauptbildschirm, drei Felder", 4.7, 8.9, 3, [k_map, k_ship, k_split])
row("B", "Wandstationen, große Schirme", 4.1, 5.5, 8, [k_split, k_orbit, k_split, k_map, k_bars, k_split, k_wave, k_split])
row("C", "Wandstationen, Statusleiste oben", 4.1, 1.4, 8, [k_keys, k_text, k_keys, k_bars])
row("D", "Wandstationen, Pultfelder", 3.3, 1.5, 8, [k_keys, k_keys, k_text, k_keys])
row("E", "Blende unter dem Fenster", 5.5, 1.9, 6, [k_wave, k_text, k_ship, k_bars, k_gauge, k_text])
row("F", "Steuerpulte, Bedienfelder", 3.6, 1.4, 6, [k_keys, k_gauge, k_keys])
row("G", "Geländer, Anzeigen", 3.3, 1.2, 3, [k_keys, k_text, k_keys])
row("H", "Kommandosessel, Armlehnen", 3.3, 1.0, 2, [k_keys, k_keys])
row("I", "Stehpult unter Hauptschirm", 12.2, 1.4, 1, [k_keys])
row("J", "Rückwand, Bildschirmsäulen", 3.6, 3.3, 12, [k_text, k_bars, k_orbit, k_text, k_gauge, k_map])
row("K", "Lifttüren", 7.7, 15.0, 2, None, special=lambda x, y_, w, h, i: door(x, y_, w, h, i + 1))


def extras(x, y_, w, h, i):
    if i == 0:
        sign(x, y_, w, h, "DECK 1 · BRÜCKE", "#1d3557")
    elif i == 1:
        sign(x, y_, w, h, "PERIHELION DSV-27", "#141414", "#ffcc00")
    else:
        sign(x, y_, w, h, "NOTAUSSTIEG", "#c8102e")


row("L", "Schilder für freie Wandflächen", 12.0, 1.8, 3, None, special=extras)

# ------------------------------------------------------------------ placement plan (do not cut out)
py0 = y + 6
T(12, py0, "Einbauplan (Draufsicht, nicht ausschneiden) – oben = Flugrichtung, unten = Rückwand", 3.0, INK, weight="bold")
S = 1.75                                   # mm per design unit
ox, oy = 105.0, py0 + 6 + 33.4 * S         # sphere centre on the page


def pp(xd, yd):                            # design x (forward), y (side) -> page
    return ox + yd * S, oy - xd * S


def arc(cx, cy, r, a0, a1, col="#333", sw=0.35, n=40):
    P([pp(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
       for i in range(n + 1)], col, sw)


def lab(xd, yd, s, dx=0.0, dy=0.0):
    px, py = pp(xd, yd)
    C(px + dx, py + dy, 2.3, fill="#c8102e")
    T(px + dx, py + dy + 1.0, s, 3.0, WH, "middle", "bold")


a_end = math.degrees(math.acos(6.0 / 33.4))
arc(0, 0, 33.4, -a_end, a_end, "#111", 0.6, 80)                       # hull
P([pp(6, -32.9), pp(6, 32.9)], "#111", 0.6)                           # rear bulkhead
arc(20, 0, 9.5, 0, 360, "#666", 0.25, 80)                             # command well
arc(20, 0, 10.2, 118, 242, "#222", 0.9)                               # rail
arc(0, 0, 31.5, -41, 41, "#222", 1.6)                                 # hood
for sy in (-1, 1):
    arc(0, 0, 32.0, sy * 47, sy * 84, "#222", 1.4)                    # display wall
    arc(0, 0, 29.4, sy * 47, sy * 84, "#888", 1.2)                    # desk
    arc(14.5, 0, 10.5, sy * 5, sy * 40, "#222", 1.6)                  # flight desks
    px, py = pp(14.5 + 6.4 * math.cos(math.radians(30)), sy * 6.4 * math.sin(math.radians(30)))
    R(px - 2.6, py - 2.6, 5.2, 5.2, "#bbb", rx=0.8)
    for yc in (13.5,):
        px, py = pp(7.2, sy * yc)
        R(px - 5.5, py - 1.0, 11.0, 2.0, "#888")
    for yc in (21.0, 26.0):
        px, py = pp(7.2, sy * yc)
        R(px - 2.8, py - 1.0, 5.6, 2.0, "#444")
px, py = pp(14.5, 0)
R(px - 3.6, py - 3.6, 7.2, 7.2, "#bbb", rx=0.8)
for sy in (-1, 1):
    R(px + sy * 5.6 - 1.2, py - 3.4, 2.4, 6.8, "#555")
px, py = pp(7.2, 0)
R(px - 10.5, py - 1.0, 21.0, 2.0, "#222")
px, py = pp(8.6, 0)
R(px - 8.5, py - 1.6, 17.0, 1.4, "#888")
lab(7.2, 0, "A", 0, 5.2)
lab(8.6, 0, "I", 9.5, 4.0)
lab(32.0 * math.cos(math.radians(66)), 32.0 * math.sin(math.radians(66)), "B", 5.5, -1)
lab(32.0 * math.cos(math.radians(52)), 32.0 * math.sin(math.radians(52)), "C", 5.5, -1)
lab(29.4 * math.cos(math.radians(66)), -29.4 * math.sin(math.radians(66)), "D", 6.0, 3.5)
lab(31.5, 0, "E", 0, -5.0)
lab(14.5 + 10.5 * math.cos(math.radians(22)), 10.5 * math.sin(math.radians(22)), "F", 5.0, -3.0)
lab(20 - 10.2, 0, "G", 0, 0)
lab(14.5, 3.2, "H", 0, 0)
lab(7.2, 23.5, "J", 0, 5.2)
lab(7.2, -23.5, "J", 0, 5.2)
lab(7.2, 13.5, "K", 0, 5.2)
lab(7.2, -13.5, "K", 0, 5.2)
ny = oy + 6 + 9
notes = ["A, B, C, J, K sitzen senkrecht an den Wänden (in den vertieften Feldern), D–I liegen flach auf den Pulten.",
         "B = großes Feld, C = schmale Leiste direkt darüber. L = frei verteilen, z. B. über den Türen.",
         "Transparentes Decalpapier: vertiefte Felder vorher weiß oder silbern streichen, sonst bleiben die Farben dunkel."]
for i, s in enumerate(notes):
    T(12, ny + i * 4.2, s, 2.6, "#333")
out.append("</svg>")
open("decals_innen.svg", "w").write("\n".join(out))
print("rows end y =", round(y, 1), "plan end y =", round(ny + 12, 1))
