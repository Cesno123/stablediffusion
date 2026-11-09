"""Generate the next post image when the queue is empty.

Combines a random scene from prompt_library.py that has not been used yet
(posted/used_prompts.txt; starts over once all are used) with a random visual
style that was not among the last few (posted/used_styles.txt), renders it
with FLUX.2 [max], adds a fine paper/film grain against the smooth digital
look and saves it to queue/ for post_queue.py. Needs BFL_API_KEY.
"""

import datetime as dt
import io
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bfl import generate  # noqa: E402
from post_queue import IMAGES, QUEUE, queue_files, video_turn  # noqa: E402
from prompt_library import SCENES, STYLE_ENDING, STYLES  # noqa: E402

USED = os.path.join(HERE, "posted", "used_prompts.txt")
USED_STYLES = os.path.join(HERE, "posted", "used_styles.txt")
RECENT_STYLES = 12  # a style comes back only after this many other posts
MODEL = os.environ.get("SPACEAGE_MODEL", "flux2max")


def add_grain(data, seed, strength=5.0):
    """Fine, slightly clumpy monochrome grain (like paper or film) on a JPEG; returns JPEG bytes."""
    import numpy as np
    from PIL import Image, ImageFilter

    img = Image.open(io.BytesIO(data)).convert("RGB")
    rng = np.random.default_rng(seed)
    fine = rng.normal(0, 1, (img.height, img.width))
    coarse = Image.fromarray(np.uint8(np.clip(rng.normal(128, 40, (img.height // 3 + 1, img.width // 3 + 1)), 0, 255)))
    coarse = np.asarray(coarse.resize(img.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(1)), float) / 40 - 3.2
    grain = (0.7 * fine + 0.3 * coarse) * strength
    out = np.clip(np.asarray(img, float) + grain[:, :, None], 0, 255).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(out).save(buf, "JPEG", quality=94)
    return buf.getvalue()


def queue_has_media():
    """Something to post this round: an image, or a video whose turn it is (waiting videos don't count)."""
    return bool(queue_files(IMAGES)) or video_turn()


def main():
    if queue_has_media():
        print("queue not empty - nothing generated")
        return
    key = os.environ.get("BFL_API_KEY", "").strip()
    if not key:
        sys.exit("BFL_API_KEY is not set")
    used = set()
    if os.path.exists(USED):
        with open(USED) as f:
            used = {line.strip() for line in f if line.strip()}
    fresh = [p for p in SCENES if p[0] not in used]
    if not fresh:  # every prompt used once: start a new round
        used, fresh = set(), list(SCENES)
        open(USED, "w").close()
    recent = []
    if os.path.exists(USED_STYLES):
        with open(USED_STYLES) as f:
            recent = [line.strip() for line in f if line.strip()][-RECENT_STYLES:]
    rng = random.Random()
    for title, scene in rng.sample(fresh, min(3, len(fresh))):  # retry with another prompt on failure
        style, look = rng.choice([s for s in STYLES if s[0] not in recent] or STYLES)
        prompt = f"{scene} {look}. {STYLE_ENDING}"
        print(f"generating '{title}' as '{style}' with {MODEL}", flush=True)
        try:
            data = generate(prompt, MODEL, key, rng.randrange(2**31))
        except RuntimeError as e:
            print(f"  failed: {e}", flush=True)
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", f"{title} {style}".lower()).strip("-")
        path = os.path.join(QUEUE, f"auto-{dt.datetime.utcnow():%Y%m%d-%H%M}-{slug}.jpg")
        with open(path, "wb") as f:
            f.write(add_grain(data, rng.randrange(2**31)))
        os.makedirs(os.path.dirname(USED), exist_ok=True)
        with open(USED, "a") as f:
            f.write(title + "\n")
        with open(USED_STYLES, "a") as f:
            f.write(style + "\n")
        print(f"saved {os.path.relpath(path, HERE)}")
        return
    sys.exit("no image could be generated")


USED_FLUX = os.path.join(HERE, "posted", "used_flux.txt")


def batch(count, which="comic"):
    """Generate count new images into the queue right away (run.py --flux), whatever the queue holds.

    which: "comic" (comic_prompts.py, each prompt once before any repeats), "fifties" (only the
    1950s comic prompts, which do best on the account) or "library" (a scene
    from prompt_library.py in a random style, like the automatic images). Stops early when the
    FLUX balance is empty. Returns a short report."""
    from comic_prompts import COMIC

    key = os.environ.get("BFL_API_KEY", "").strip()
    if not key:
        return "FLUX: BFL_API_KEY fehlt"
    rng = random.Random()
    used = set()
    if os.path.exists(USED_FLUX):
        with open(USED_FLUX) as f:
            used = {line.strip() for line in f if line.strip()}
    made, errors = [], []
    for _ in range(count):
        if which in ("comic", "fifties"):
            pool = [c for c in COMIC if which == "comic" or c[0].startswith("fifties")]
            fresh = [c for c in pool if c[0] not in used] or pool
            title, prompt = rng.choice(fresh)
            prompt += " Comic book art, printed on paper. Not a photo, not a 3D render, no text, no speech bubbles."
        else:
            title, scene = rng.choice(SCENES)
            style, look = rng.choice(STYLES)
            title = f"{title} {style}"
            prompt = f"{scene} {look}. {STYLE_ENDING}"
        try:
            data = generate(prompt, MODEL, key, rng.randrange(2**31))
        except RuntimeError as e:
            errors.append(str(e)[:120])
            if "402" in str(e) or "credit" in str(e).lower() or len(errors) >= 3:
                break
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        path = os.path.join(QUEUE, f"flux-{dt.datetime.utcnow():%Y%m%d-%H%M%S}-{slug}.jpg")
        with open(path, "wb") as f:
            f.write(add_grain(data, rng.randrange(2**31)))
        os.makedirs(os.path.dirname(USED_FLUX), exist_ok=True)
        with open(USED_FLUX, "a") as f:
            f.write(title + "\n")
        used.add(title)
        made.append(os.path.basename(path))
        print(f"  {len(made)}/{count}: {made[-1]}", flush=True)
    report = f"FLUX: {len(made)} von {count} Bildern in die Warteschlange gelegt"
    return report + (f" (Fehler: {'; '.join(errors)})" if errors else "")


if __name__ == "__main__":
    main()
