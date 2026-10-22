"""Take the next file from spaceage/queue/ and prepare it for posting.

Images (png/jpg/webp) become a feed photo: converted to JPEG and cropped to
Instagram's tallest allowed ratio (4:5) if needed. Videos (mp4/mov) become a
reel. The oldest upload (by git history) goes first.

Caption: queue/<name>.txt if it exists, otherwise one is generated.
The original, the prepared file and the caption move to posted/.
Prints key=value lines for $GITHUB_OUTPUT.
"""

import argparse
import datetime as dt
import os
import random
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue")
POSTED = os.path.join(HERE, "posted")
IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEOS = {".mp4", ".mov"}

HOOKS = [
    "Cover art from a book that was never written.",
    "Found on a paperback from 2187.",
    "Which mission would you join?",
    "They built it to last a thousand years.",
    "Departure in T-minus 10. 🚀",
    "Retro future, rendered today.",
    "Would you live here?",
    "Last transmission before the jump.",
    "Somewhere beyond the outer rim.",
    "Not all who wander are lost in space.",
]
TAGS = ("#scifi #scifiart #retrofuturism #80sscifi #vintagescifi #spaceart "
        "#conceptart #aiart #midjourney #spaceage42")


def added_at(path):
    """Unix time the file was first committed (upload order); mtime as fallback."""
    out = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%ct", "--", path],
        capture_output=True, text=True, cwd=HERE,
    ).stdout.split()
    return int(out[-1]) if out else int(os.path.getmtime(path))


def next_file():
    if not os.path.isdir(QUEUE):
        return None
    files = [os.path.join(QUEUE, f) for f in os.listdir(QUEUE)
             if os.path.splitext(f)[1].lower() in IMAGES | VIDEOS]
    return min(files, key=lambda p: (added_at(p), p)) if files else None


def caption_for(src):
    txt = os.path.splitext(src)[0] + ".txt"
    if os.path.exists(txt):
        with open(txt) as f:
            return f.read().strip()
    rng = random.Random(os.path.basename(src))
    return f"{rng.choice(HOOKS)}\n\n{TAGS}"


def to_feed_jpeg(src, dst):
    img = Image.open(src).convert("RGB")
    w, h = img.size
    if w / h < 0.8:  # taller than 4:5 is rejected for feed photos
        nh = int(w / 0.8)
        top = (h - nh) // 2
        img = img.crop((0, top, w, top + nh))
    if img.width > 1440:
        img = img.resize((1440, round(img.height * 1440 / img.width)), Image.LANCZOS)
    img.save(dst, "JPEG", quality=92, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="only report what would be posted")
    args = ap.parse_args()

    src = next_file()
    if not src:
        print("kind=none")
        return
    name = os.path.basename(src)
    caption = caption_for(src)
    ext = os.path.splitext(name)[1].lower()
    kind = "image" if ext in IMAGES else "video"
    if args.dry_run:
        print(f"kind={kind}\nsource={name}", file=sys.stdout)
        print(f"--- caption ---\n{caption}", file=sys.stderr)
        return

    os.makedirs(POSTED, exist_ok=True)
    stem = f"{dt.date.today():%Y%m%d}-{os.path.splitext(name)[0]}"
    media = os.path.join(POSTED, stem + (".jpg" if kind == "image" else ext))
    if kind == "image":
        to_feed_jpeg(src, media)
        os.remove(src)
    else:
        shutil.move(src, media)
    txt = os.path.splitext(src)[0] + ".txt"
    if os.path.exists(txt):
        os.remove(txt)
    caption_path = os.path.join(POSTED, stem + ".txt")
    with open(caption_path, "w") as f:
        f.write(caption + "\n")

    rel = lambda p: os.path.relpath(p, os.path.dirname(HERE))  # noqa: E731
    print(f"kind={kind}\nsource={name}\nmedia={rel(media)}\ncaption={rel(caption_path)}")


if __name__ == "__main__":
    main()
