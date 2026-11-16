"""Zeichnet Banner (320x180) und Symbol (192x192) im Röhrenkiste-Stil."""
from PIL import Image, ImageDraw, ImageFont
import os, sys
out = sys.argv[1]
ORANGE, BG, TV, BEZEL = (227, 165, 72), (21, 18, 15), (43, 46, 51), (185, 188, 192)
BARS = [(192,192,192),(192,192,0),(0,192,192),(0,192,0),(192,0,192),(192,0,0),(0,0,192)]

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def tv(d, x, y, w, h):
    d.rounded_rectangle([x, y, x + w, y + h], radius=w // 9, fill=TV)
    sx, sy, sw, sh = x + w * .1, y + h * .1, w * .8, h * .62
    d.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=w // 14, fill=BEZEL)
    ix, iy, iw, ih = sx + 4, sy + 4, sw - 8, sh - 8
    for i, c in enumerate(BARS):
        d.rectangle([ix + iw * i / 7, iy, ix + iw * (i + 1) / 7, iy + ih], fill=c)
    d.ellipse([x + w * .72, y + h * .8, x + w * .8, y + h * .9], fill=(255, 59, 47))
    for i in range(5):
        d.line([x + w * .14 + i * w * .08, y + h * .85, x + w * .18 + i * w * .08, y + h * .85], fill=(20, 20, 20), width=3)

b = Image.new("RGB", (320, 180), BG); d = ImageDraw.Draw(b)
tv(d, 14, 30, 120, 120)
d.text((146, 62), "RÖHREN", font=font(30), fill=ORANGE)
d.text((146, 96), "KISTE", font=font(30), fill=ORANGE)
d.text((148, 136), "TV 1970–2015", font=font(13), fill=(163, 150, 132))
b.save(os.path.join(out, "banner.png"), optimize=True)

i = Image.new("RGBA", (192, 192), (0, 0, 0, 0)); d = ImageDraw.Draw(i)
tv(d, 8, 8, 176, 176)
i.save(os.path.join(out, "icon.png"), optimize=True)
