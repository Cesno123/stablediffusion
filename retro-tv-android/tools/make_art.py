"""Zeichnet Symbol (512x512) und Banner (640x360) einer Fire-TV-App.

Aufruf: make_art.py ZIELORDNER "ZEILE1|ZEILE2|UNTERZEILE" HINTERGRUND AKZENT
Der Fire-TV-Startbildschirm schneidet das quadratische Symbol auf 16:9 zu: Fernseher
und Name liegen deshalb im mittleren Streifen, der Rest ist nur Hintergrundfarbe.
Gezeichnet wird in dreifacher Größe und dann verkleinert (glatte Kanten).
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

out = sys.argv[1]
L1, L2, SUB = (sys.argv[2] if len(sys.argv) > 2 else "RÖHREN|KISTE|TV 1970–2015").split("|")
BG = sys.argv[3] if len(sys.argv) > 3 else "#1a1410"
ACCENT = sys.argv[4] if len(sys.argv) > 4 else "#e8a33d"
SS = 3  # Supersampling

FONT_BOLD = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf"
FONT_SUB = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
BARS = [(200, 200, 200), (206, 196, 20), (20, 196, 206), (24, 190, 60), (196, 34, 196), (208, 36, 36), (36, 44, 200)]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", size)


def fit(text, path, max_w, max_size):
    size = max_size
    while size > 8:
        f = font(path, size)
        if f.getbbox(text)[2] <= max_w:
            return f
        size -= 2
    return font(path, size)


def background(img, bg):
    """Senkrechter Verlauf plus feine Zeilen wie auf einer Röhre."""
    w, h = img.size
    d = ImageDraw.Draw(img)
    top, bottom = mix(bg, (255, 255, 255), .07), mix(bg, (0, 0, 0), .35)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=mix(top, bottom, y / h))
    for y in range(0, h, 4 * SS):
        d.line([(0, y), (w, y)], fill=mix(mix(top, bottom, y / h), (0, 0, 0), .18), width=SS)


def television(img, x, y, w, accent):
    """Röhrenfernseher (70er): Holzfarbenes Gehäuse, Bildröhre mit Testbild, Knöpfe, Antenne, Füße."""
    h = round(w * .72)
    d = ImageDraw.Draw(img)
    # Antenne
    ax, ay = x + w * .5, y + h * .02
    d.line([(ax, ay), (ax - w * .22, y - h * .26)], fill=(210, 210, 210), width=round(w * .018))
    d.line([(ax, ay), (ax + w * .18, y - h * .30)], fill=(210, 210, 210), width=round(w * .018))
    d.ellipse([ax - w * .05, ay - w * .03, ax + w * .05, ay + w * .03], fill=(70, 70, 70))
    # Füße
    for fx in (x + w * .16, x + w * .78):
        d.polygon([(fx, y + h), (fx + w * .06, y + h), (fx + w * .03, y + h * 1.14)], fill=(84, 52, 30))
    # Schatten + Gehäuse
    shadow = Image.new("L", img.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle([x + w * .03, y + h * .06, x + w * 1.03, y + h * 1.06], radius=w * .1, fill=150)
    img.paste((0, 0, 0), mask=shadow.filter(ImageFilter.GaussianBlur(w * .04)))
    case = (122, 74, 40)
    d.rounded_rectangle([x, y, x + w, y + h], radius=w * .1, fill=case)
    d.rounded_rectangle([x + w * .02, y + h * .03, x + w * .98, y + h * .5], radius=w * .08, fill=mix(case, (255, 255, 255), .12))
    d.rounded_rectangle([x + w * .02, y + h * .45, x + w * .98, y + h * .97], radius=w * .08, fill=mix(case, (0, 0, 0), .08))
    # Bildröhre
    sx0, sy0, sx1, sy1 = x + w * .07, y + h * .1, x + w * .71, y + h * .9
    d.rounded_rectangle([sx0 - w * .02, sy0 - w * .02, sx1 + w * .02, sy1 + w * .02], radius=w * .1, fill=(28, 28, 30))
    screen = Image.new("RGB", (round(sx1 - sx0), round(sy1 - sy0)))
    sd = ImageDraw.Draw(screen)
    bw = screen.width / len(BARS)
    for i, c in enumerate(BARS):
        sd.rectangle([i * bw, 0, (i + 1) * bw, screen.height * .72], fill=c)
    for i, c in enumerate(reversed(BARS)):
        sd.rectangle([i * bw, screen.height * .72, (i + 1) * bw, screen.height], fill=mix(c, (0, 0, 0), .55))
    lines = Image.new("L", screen.size, 0)   # Bildzeilen, nur leicht abgedunkelt
    for yy in range(0, screen.height, 4 * SS):
        ImageDraw.Draw(lines).line([(0, yy), (screen.width, yy)], fill=70, width=SS)
    screen.paste((0, 0, 0), mask=lines)
    # Wölbung: Vignette + Glanzlicht
    vign = Image.new("L", screen.size, 0)
    ImageDraw.Draw(vign).rounded_rectangle([screen.width * .03, screen.height * .04, screen.width * .97, screen.height * .96],
                                           radius=screen.width * .2, fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(screen.width * .035))
    screen = Image.composite(screen, Image.new("RGB", screen.size, (10, 10, 12)), vign)
    gloss = Image.new("L", screen.size, 0)
    ImageDraw.Draw(gloss).ellipse([-screen.width * .2, -screen.height * .6, screen.width * .9, screen.height * .35], fill=70)
    screen.paste((255, 255, 255), mask=gloss.filter(ImageFilter.GaussianBlur(screen.width * .05)))
    mask = Image.new("L", screen.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, screen.width - 1, screen.height - 1], radius=w * .08, fill=255)
    img.paste(screen, (round(sx0), round(sy0)), mask)
    # Bedienfeld: zwei Drehknöpfe, Lautsprechergitter, Kontrolllampe in Akzentfarbe
    px = x + w * .8
    for ky in (y + h * .22, y + h * .44):
        r = w * .065
        d.ellipse([px - r, ky - r, px + r, ky + r], fill=(46, 40, 36))
        d.ellipse([px - r * .7, ky - r * .7, px + r * .7, ky + r * .7], fill=(196, 190, 180))
        d.line([(px, ky), (px + r * .55, ky - r * .45)], fill=(46, 40, 36), width=round(w * .014))
    for i in range(4):
        gy = y + h * (.62 + i * .06)
        d.line([(px - w * .08, gy), (px + w * .08, gy)], fill=(58, 34, 18), width=round(w * .016))
    lr = w * .025
    d.ellipse([px - lr, y + h * .86 - lr, px + lr, y + h * .86 + lr], fill=accent)


def compose(W, H, bg, accent, band_top, band_h):
    """Zeichnet Fernseher + Schrift in einen waagerechten Streifen."""
    img = Image.new("RGB", (W, H))
    background(img, bg)
    tv_w = band_h * .78
    television(img, W * .06, band_top + band_h * .26, tv_w, accent)
    d = ImageDraw.Draw(img)
    tx = W * .06 + tv_w + W * .05
    max_w = W - tx - W * .05
    f1 = fit(L1, FONT_BOLD, max_w, round(band_h * .27))
    f2 = fit(L2, FONT_BOLD, max_w, round(band_h * .27))
    size = min(f1.size, f2.size)
    f = font(FONT_BOLD, size)
    y1 = band_top + band_h * .16
    for i, line in enumerate((L1, L2)):
        yy = y1 + i * size * 1.05
        d.text((tx + SS * 3, yy + SS * 3), line, font=f, fill=mix(bg, (0, 0, 0), .6))   # Schlagschatten
        d.text((tx, yy), line, font=f, fill=accent)
    fs = fit(SUB, FONT_SUB, max_w, round(band_h * .1))
    d.text((tx + SS, y1 + size * 2.25), SUB, font=fs, fill=mix(accent, (255, 255, 255), .55))
    return img


bg, accent = rgb(BG), rgb(ACCENT)
# Symbol 512x512: Inhalt im mittleren 16:9-Streifen (y 128..384)
S = 512 * SS
compose(S, S, bg, accent, S * .25, S * .5).resize((512, 512), Image.LANCZOS).save(os.path.join(out, "icon.png"), optimize=True)
# Banner 640x360 (xhdpi-Banner 320x180, doppelte Auflösung)
compose(640 * SS, 360 * SS, bg, accent, 0, 360 * SS).resize((640, 360), Image.LANCZOS).save(os.path.join(out, "banner.png"), optimize=True)
