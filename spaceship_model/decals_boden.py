#!/usr/bin/env python3
"""Floor decals for the bridge insert (part 04) of the 100 cm model: A4, scale 1:1, sizes in mm.

Usage:  python3 decals_boden.py  -> decals_boden.svg  (needs shapely; print at 100 %)
The floor is covered by six pieces that are cut to go around the furniture. Two sets (spares).
"""
import math
from shapely.geometry import Point, box, LineString
from shapely.ops import unary_union
from shapely import affinity

K = 1.125 * 1.2346                         # design units -> mm on the 100 cm model
SHRINK = 0.25 / K                          # every piece is 0.25 mm smaller all round
FONT = "DejaVu Sans, Liberation Sans, Arial, sans-serif"
BLUE, BLUE2, GREY, GREY2, AMB, RED, INK = "#22344f", "#3d5a85", "#9aa0a9", "#6c727c", "#ffb300", "#c8102e", "#141414"


def disc(x, y, r):
    return Point(x, y).buffer(r, 96)


def ring(x, y, r0, r1):
    return disc(x, y, r1).difference(disc(x, y, r0))


def half(sy):                              # sy = +1: y > 0
    return box(-50, 0, 50, 50) if sy > 0 else box(-50, -50, 50, 0)


CX, WX = 14.5, 20.0
seat = [(CX + 6.4 * math.cos(math.radians(30)), sy * 6.4 * math.sin(math.radians(30))) for sy in (1, -1)]
furn = unary_union([disc(CX, 0, 3.85), box(12.0, -4.2, 17.4, 4.2)]
                   + [disc(x, y, 2.15) for x, y in seat]
                   + [box(x - 2.15, min(0, y), x + 2.15, max(0, y)) for x, y in seat])
well = disc(WX, 0, 9.3).intersection(disc(CX, 0, 9.2)).difference(furn)
gallery = box(8.8, -40, 19.8, 40).difference(disc(WX, 0, 11.3)).intersection(disc(0, 0, 23.2))
front = disc(0, 0, 28.0).intersection(box(20.2, -40, 40, 40)).difference(disc(CX, 0, 11.9))

# pattern layers in design coordinates: (colour, geometry), drawn in this order and clipped to the piece
pat_well = [(BLUE, box(-50, -50, 50, 50)),
            (BLUE2, unary_union([ring(CX, 0, r, r + 0.28) for r in (4.6, 5.9, 7.2)])),
            (AMB, ring(WX, 0, 8.75, 9.6)),
            (AMB, ring(CX, 0, 8.75, 9.6))]
spokes = unary_union([LineString([(WX, 0), (WX + 40 * math.cos(math.radians(a)), 40 * math.sin(math.radians(a)))]).buffer(0.09)
                      for a in range(100, 261, 16)])
pat_gal = [(GREY, box(-50, -50, 50, 50)),
           (GREY2, spokes),
           (GREY2, unary_union([ring(WX, 0, r, r + 0.18) for r in (14.5, 18.0)])),
           (RED, ring(WX, 0, 11.3, 12.0)),
           (INK, ring(WX, 0, 12.0, 12.2))]
pat_front = [(BLUE, box(-50, -50, 50, 50)),
             (BLUE2, unary_union([ring(CX, 0, r, r + 0.22) for r in (13.4, 15.0, 16.6, 18.2)])),
             (AMB, ring(CX, 0, 11.9, 12.5))]

pieces = []                                # (letter, piece, pattern)
for name, shape, pat in (("M", well, pat_well), ("N", gallery, pat_gal), ("O", front, pat_front)):
    for sy, side in ((-1, "links"), (1, "rechts")):
        p = shape.intersection(half(sy)).buffer(-SHRINK)
        if p.geom_type != "Polygon":
            p = max(p.geoms, key=lambda g: g.area)
        pieces.append((name, side, p, pat))

out = []


def path(geom, ox, oy, fill, stroke="none", sw=0.0):
    """Design coords -> page: forward (x) points up, y to the right."""
    polys = [geom] if geom.geom_type == "Polygon" else [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
    d = []
    for g in polys:
        for r in [g.exterior] + list(g.interiors):
            pts = [(ox + y * K, oy - x * K) for x, y in r.coords]
            d.append("M" + " L".join(f"{a:.3f},{b:.3f}" for a, b in pts) + " Z")
    if d:
        out.append(f'<path d="{" ".join(d)}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{sw}"/>')


def T(x, y, s, size, col=INK, anchor="start", weight="normal"):
    out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size:.2f}" font-weight="{weight}" '
               f'text-anchor="{anchor}" fill="{col}">{s}</text>')


def draw_set(ox, oy, spread):
    """One complete floor, pieces pulled apart by spread (design units) so they can be cut out."""
    for name, side, p, pat in pieces:
        sy = -1 if side == "links" else 1
        dx = {"M": 0.0, "N": -2.5 * spread, "O": 2.2 * spread}[name]
        dy = sy * spread * {"M": 1.0, "N": 2.4, "O": 1.6}[name]
        for col, g in pat:
            path(affinity.translate(g.intersection(p), dx, dy), ox, oy, col)
        path(affinity.translate(p, dx, dy), ox, oy, "none", "#777", 0.06)


W, H = 210.0, 297.0
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">')
out.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
T(12, 14, "PERIHELION · Boden-Decals Brücke (Teil 04) · Modell 100 cm · Maßstab 1:1 · mit 100 % drucken", 3.6, weight="bold")
T(12, 19, "Zwei komplette Sätze (einer als Reserve). Jeder Satz: 6 Teile, an der grauen Linie ausschneiden.", 2.8, "#444")
for i, ox in enumerate((58.0, 152.0)):
    T(ox, 28, f"Satz {i + 1}", 3.2, weight="bold", anchor="middle")
    draw_set(ox, 84.0, 1.6)

# placement plan, twice the real size, pieces in place
py = 112.0
T(12, py, "Einbauplan (doppelte Größe, nicht ausschneiden) – oben = Flugrichtung, unten = Rückwand", 3.0, weight="bold")
ox, oy = 105.0, py + 6 + 33.4 * K * 2
K0 = K
K = K0 * 2
a_end = math.acos(6.0 / 33.4)
arcpts = [(33.4 * math.cos(-a_end + 2 * a_end * i / 80), 33.4 * math.sin(-a_end + 2 * a_end * i / 80)) for i in range(81)]
hull = LineString(arcpts + [arcpts[0]]).buffer(0.25)
path(hull, ox, oy, "#111")
def sector(a0, a1, r=60.0):
    from shapely.geometry import Polygon
    return Polygon([(0, 0)] + [(r * math.cos(math.radians(a0 + (a1 - a0) * i / 30)), r * math.sin(math.radians(a0 + (a1 - a0) * i / 30)))
                               for i in range(31)])


blocks = unary_union([furn, ring(CX, 0, 9.4, 11.6).intersection(box(CX, -40, 40, 40)),
                      ring(WX, 0, 9.8, 11.0).intersection(box(0, -40, 15.2, 40)),
                      ring(0, 0, 29.6, 33.2).intersection(sector(-41, 41)),
                      ring(0, 0, 28.2, 33.2).intersection(sector(47, 84).union(sector(-84, -47))),
                      box(6, -33, 8.6, 33)] + [disc(25.2 * math.cos(math.radians(a)), s * 25.2 * math.sin(math.radians(a)), 1.9)
                                               for a in (56, 72) for s in (-1, 1)]).intersection(box(6, -40, 40, 40))
path(blocks.intersection(disc(0, 0, 33.2)), ox, oy, "#d5d8dd")
for name, side, p, pat in pieces:
    for col, g in pat:
        path(g.intersection(p), ox, oy, col)
    c = p.representative_point()
    px, pyy = ox + c.y * K, oy - c.x * K
    out.append(f'<circle cx="{px:.2f}" cy="{pyy:.2f}" r="2.6" fill="#fff" stroke="{RED}" stroke-width="0.5"/>')
    T(px, pyy + 1.1, name, 3.2, RED, "middle", "bold")
K = K0
ny = oy + 2
notes = ["M = Kommandomulde (zwei Hälften, Naht in der Schiffsmitte). Aussparungen: Podest des Kommandosessels und die Sesselfüße.",
         "N = Galerie links und rechts (rote Kante zeigt zum Geländer). O = Boden vor den Steuerpulten (gelbe Kante zum Pult).",
         "Hellgrau im Plan = Möbel und Wände, dort liegt kein Decal. Teile sind rundum 0,25 mm kleiner als die freie Fläche.",
         "Transparentes Decalpapier: Boden vorher hell streichen (weiß oder hellgrau), sonst wirken Blau und Rot fast schwarz."]
for i, s in enumerate(notes):
    T(12, ny + 8 + i * 4.4, s, 2.6, "#333")
out.append("</svg>")
open("decals_boden.svg", "w").write("\n".join(out))
for name, side, p, _ in pieces:
    b = p.bounds
    print(name, side, f"{(b[3]-b[1])*K:.1f} x {(b[2]-b[0])*K:.1f} mm, area {p.area*K*K:.0f} mm2")
print("plan bottom", ny + 8 + 4 * 4.4)
