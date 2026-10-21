"""Render a vertical sci-fi reel (1080x1920 MP4 with sound) on a plain CPU.

Pipeline:
  1. pick an idea (style, subject, 3 shot prompts) from ideas.py
  2. generate 3 keyframes with SD-Turbo (or procedural art with --no-ai)
  3. animate them: slow zoom/pan, cross-fades, style effects, text overlay
  4. synthesize an ambient drone soundtrack
  5. encode with ffmpeg

Outputs in --out: reel.mp4, caption.txt, meta.json, keyframe_*.png
"""

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
import textwrap
import wave
from dataclasses import asdict

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ideas import make_idea  # noqa: E402

W, H = 1080, 1920
FPS = 30
GEN_W, GEN_H = 512, 896  # ~9:16, multiple of 64
HANDLE = "@_spaceage42"
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


# ---------------------------------------------------------------- keyframes

def generate_ai(prompts, seed, steps, model):
    import torch
    from diffusers import AutoPipelineForText2Image

    torch.set_num_threads(os.cpu_count() or 4)
    pipe = AutoPipelineForText2Image.from_pretrained(model, torch_dtype=torch.float32)
    pipe.set_progress_bar_config(disable=True)
    images = []
    for i, prompt in enumerate(prompts):
        print(f"[keyframe {i + 1}/{len(prompts)}] {prompt}", flush=True)
        gen = torch.Generator("cpu").manual_seed(seed + i)
        img = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=0.0,
            width=GEN_W,
            height=GEN_H,
            generator=gen,
        ).images[0]
        images.append(img)
    return images


def generate_procedural(seed, count=3):
    """Fallback art without any model: sky gradient, stars, planet, skyline."""
    images = []
    for i in range(count):
        rng = np.random.default_rng(seed + i)
        top, bottom = rng.integers(0, 120, 3), rng.integers(60, 255, 3)
        t = np.linspace(0, 1, GEN_H)[:, None, None]
        arr = (top * (1 - t) + bottom * t**2).repeat(GEN_W, axis=1)
        stars = rng.random((GEN_H, GEN_W)) > 0.996
        arr[stars] = 255
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        r = int(rng.integers(60, 220))
        cx, cy = int(rng.integers(0, GEN_W)), int(rng.integers(100, GEN_H // 2))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c) for c in rng.integers(80, 255, 3)))
        d.ellipse([cx - r + r // 3, cy - r - r // 6, cx + r + r // 3, cy + r - r // 6], fill=tuple(int(c) for c in top))
        x = 0
        while x < GEN_W:
            bw, bh = int(rng.integers(20, 70)), int(rng.integers(80, 400))
            d.rectangle([x, GEN_H - bh, x + bw, GEN_H], fill=(5, 5, 12))
            x += bw
        images.append(img.filter(ImageFilter.GaussianBlur(0.8)))
    return images


# ---------------------------------------------------------------- animation

def cover(img, w, h):
    """Scale and center-crop img so it fully covers w x h."""
    s = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


class Effects:
    def __init__(self, names, rng):
        self.names = set(names)
        self.rng = rng
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vignette = (1 - 0.55 * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None]
        self.scan = np.where((np.arange(H) % 4) < 2, 1.0, 0.82).astype(np.float32)[:, None, None]
        self.grain = [rng.normal(0, 10, (H, W, 1)).astype(np.float32) for _ in range(6)]
        n = 350
        self.stars = np.c_[rng.uniform(-1, 1, n), rng.uniform(-1, 1, n), rng.uniform(0.05, 1, n)]

    def apply(self, f, i):
        rng = self.rng
        if "stars" in self.names:
            self.stars[:, 2] -= 0.006
            dead = self.stars[:, 2] <= 0.05
            self.stars[dead] = np.c_[rng.uniform(-1, 1, dead.sum()), rng.uniform(-1, 1, dead.sum()), np.ones(dead.sum())]
            x = (self.stars[:, 0] / self.stars[:, 2] * W / 2 + W / 2).astype(int)
            y = (self.stars[:, 1] / self.stars[:, 2] * H / 2 + H / 2).astype(int)
            ok = (x >= 0) & (x < W - 3) & (y >= 0) & (y < H - 3)
            b = (1 - self.stars[ok, 2]) * 255
            for dx in range(3):
                for dy in range(3):
                    f[y[ok] + dy, x[ok] + dx] = np.maximum(f[y[ok] + dy, x[ok] + dx], b[:, None])
        if "chroma" in self.names:
            k = 4 + int(3 * math.sin(i / 9))
            f[..., 0] = np.roll(f[..., 0], k, axis=1)
            f[..., 2] = np.roll(f[..., 2], -k, axis=1)
        if "glitch" in self.names and rng.random() < 0.07:
            for _ in range(rng.integers(2, 6)):
                y0 = rng.integers(0, H - 80)
                hgt = rng.integers(8, 80)
                f[y0:y0 + hgt] = np.roll(f[y0:y0 + hgt], rng.integers(-120, 120), axis=1)
        if "scanlines" in self.names:
            f *= self.scan
        if "flicker" in self.names:
            f *= 1 + rng.normal(0, 0.025) - (0.25 if rng.random() < 0.03 else 0)
        if "vignette" in self.names:
            f *= self.vignette
        if "grain" in self.names:
            f += self.grain[i % len(self.grain)]
        return f


def load_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def text_layer(text, size, y, width_chars):
    """RGBA overlay with centered, shadowed text; returns (rgb, alpha) float arrays."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = load_font(size)
    lines = textwrap.wrap(text, width_chars) or [""]
    lh = int(size * 1.25)
    for n, line in enumerate(lines):
        tw = d.textlength(line, font=font)
        pos = ((W - tw) / 2, y + n * lh)
        d.text((pos[0] + 3, pos[1] + 3), line, font=font, fill=(0, 0, 0, 200))
        d.text(pos, line, font=font, fill=(255, 255, 255, 255))
    a = np.asarray(layer, dtype=np.float32)
    return a[..., :3], a[..., 3:] / 255.0


def render_frames(keyframes, idea, seconds, seed):
    rng = np.random.default_rng(seed)
    n = len(keyframes)
    seg = seconds / n
    fade = 0.8
    zoom = 1.18
    sources = [cover(k, int(W * zoom), int(H * zoom)) for k in keyframes]
    moves = [(rng.choice([-1, 1]), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(n)]
    fx = Effects(idea.effects, rng)
    hook = text_layer(idea.hook, 64, int(H * 0.70), 26)
    mark = text_layer(HANDLE, 34, H - 120, 40)

    def shot(j, u):
        direction, px, py = moves[j]
        z = 1 + (zoom - 1) * (u if direction > 0 else 1 - u)
        sw, sh = sources[j].size
        cw, ch = sw / z, sh / z
        cx = sw / 2 + px * (sw - cw) / 2 * u
        cy = sh / 2 + py * (sh - ch) / 2 * u
        box = (max(0.0, cx - cw / 2), max(0.0, cy - ch / 2), min(sw, cx + cw / 2), min(sh, cy + ch / 2))
        return np.asarray(sources[j].resize((W, H), Image.BILINEAR, box=box), dtype=np.float32)

    total = int(seconds * FPS)
    for i in range(total):
        t = i / FPS
        frame = np.zeros((H, W, 3), np.float32)
        for j in range(n):
            left = 1.0 if j == 0 else np.clip((t - (j * seg - fade / 2)) / fade, 0, 1)
            right = 1.0 if j == n - 1 else np.clip(((j + 1) * seg + fade / 2 - t) / fade, 0, 1)
            w = left * right
            if w > 0:
                u = np.clip((t - j * seg + fade / 2) / (seg + fade), 0, 1)
                frame += w * shot(j, u)
        frame = fx.apply(frame, i)
        ha = np.clip(min((t - 0.4) / 0.5, (3.8 - t) / 0.5), 0, 1)
        if ha > 0:
            frame = frame * (1 - hook[1] * ha) + hook[0] * hook[1] * ha
        frame = frame * (1 - mark[1] * 0.6) + mark[0] * mark[1] * 0.6
        fade_io = min(1.0, t / 0.4, (seconds - t) / 0.5)
        yield (np.clip(frame * fade_io, 0, 255)).astype(np.uint8)


# ---------------------------------------------------------------- audio

def synth_audio(path, seconds, base_hz, cuts, seed, sr=48000):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * sr)) / sr
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t)
    chans = []
    for detune in (0.997, 1.003):
        f = base_hz * detune
        tone = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)
                + 0.3 * np.sin(2 * np.pi * f * 2.01 * t) + 0.15 * np.sin(2 * np.pi * f * 4.02 * t))
        noise = rng.normal(0, 1, t.size)
        wind = np.zeros_like(noise)
        a = 0.02
        acc = 0.0
        for k in range(0, t.size, 64):  # cheap block-wise one-pole low-pass
            acc = acc + a * (noise[k:k + 64].mean() * 8 - acc)
            wind[k:k + 64] = acc
        whoosh = np.zeros_like(t)
        for c in cuts:
            whoosh += np.exp(-((t - c) / 0.35) ** 2)
        chans.append(tone * lfo * 0.5 + wind * 0.6 + noise * whoosh * 0.08)
    sig = np.stack(chans, axis=1)
    env = np.minimum(1, np.minimum(t / 1.0, (seconds - t) / 1.0))[:, None]
    sig *= env
    sig = sig / (np.abs(sig).max() + 1e-9) * 0.7
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((sig * 32767).astype("<i2").tobytes())


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="out")
    ap.add_argument("--seed", type=int, help="default: today's date as YYYYMMDD")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--steps", type=int, default=3, help="SD-Turbo steps (1-4)")
    ap.add_argument("--model", default="stabilityai/sd-turbo")
    ap.add_argument("--no-ai", action="store_true", help="procedural keyframes, no model download")
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else int(dt.date.today().strftime("%Y%m%d"))
    os.makedirs(args.out, exist_ok=True)
    idea = make_idea(seed)
    print(f"seed={seed} style={idea.style} subject={idea.subject}", flush=True)

    if args.no_ai:
        keyframes = generate_procedural(seed)
    else:
        keyframes = generate_ai(idea.prompts, seed, args.steps, args.model)
    for i, k in enumerate(keyframes):
        k.save(os.path.join(args.out, f"keyframe_{i + 1}.png"))

    wav = os.path.join(args.out, "audio.wav")
    seg = args.seconds / len(keyframes)
    synth_audio(wav, args.seconds, idea.drone_hz, [seg * j for j in range(1, len(keyframes))], seed)

    mp4 = os.path.join(args.out, "reel.mp4")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for frame in render_frames(keyframes, idea, args.seconds, seed):
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg failed")
    os.remove(wav)

    with open(os.path.join(args.out, "caption.txt"), "w") as f:
        f.write(idea.caption)
    with open(os.path.join(args.out, "meta.json"), "w") as f:
        json.dump({"seed": seed, "ai": not args.no_ai, **asdict(idea)}, f, indent=2)
    print(f"done: {mp4}", flush=True)


if __name__ == "__main__":
    main()
