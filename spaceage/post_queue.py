"""Take the next file from spaceage/queue/ and prepare it for posting.

Images (png/jpg/webp) become a 9:16 reel (other ratios shown whole on a
blurred backdrop) with a slow 8-second zoom and a quiet synthesized space
ambience. Videos (mp4/mov) are posted as reels unchanged. The oldest upload (by git history) goes first.

Caption: queue/<name>.txt if it exists, otherwise the fixed CAPTION.
The reel is built in a temp folder (not committed, to keep the repo small);
posted/ only keeps a small preview image and the caption.
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
BUILD = os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "spaceage")
IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEOS = {".mp4", ".mov"}

# Fixed caption for every post (the owner's text). Instagram allows at most
# 30 hashtags; #nasa was dropped because it duplicates #NASA.
CAPTION = (
    "🚀 Step into the future with SpaceAge42 – your gateway to cosmic art and sci-fi "
    "visions! 🌌 Perfect for dreamers, explorers, and tech lovers. From interstellar "
    "landscapes to futuristic worlds, our gallery brings the thrill of space exploration "
    "to life. ✨\n\n"
    "#SpaceAge42 #SciFiArt #SpaceArt #FuturisticVibes #CosmicDreams #ExploreTheUniverse "
    "#DigitalArt #FutureWorlds #SciFiCommunity #AstronomyLovers #CyberpunkArt #GalaxyVibes "
    "#StarsAndBeyond #NewWorlds #DeepSpaceDreams #SciFiUniverse #SpaceExploration "
    "#OuterSpaceArt #StellarVisions #NextFrontier #NASA #SpaceX #StarWarsFans "
    "#StarTrekUniverse #MarsMission #space #astronomy #starwars #startrek #dystopian"
)


def added_at(path):
    """Unix time the file was first committed (upload order); mtime as fallback."""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%ct", "--", path],
            capture_output=True, text=True, cwd=HERE,
        ).stdout.split()
    except OSError:  # no git (own server)
        out = []
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
    return CAPTION


REEL_W, REEL_H, REEL_SECONDS, FPS = 1080, 1920, 8, 30


def ffmpeg_exe():
    """Bundled ffmpeg from imageio-ffmpeg (no apt needed), else the system one."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


ZOOM = 0.08  # total zoom over the clip: slow and subtle


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def reel_frame(img):
    """9:16 frame. Near-9:16 images fill it; others are shown whole on a blurred copy."""
    if abs(img.width / img.height - REEL_W / REEL_H) < 0.03:
        return cover(img, REEL_W, REEL_H)
    from PIL import ImageEnhance, ImageFilter

    bg = cover(img, REEL_W, REEL_H).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    s = min(REEL_W / img.width, REEL_H / img.height)
    fg = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    bg.paste(fg, ((REEL_W - fg.width) // 2, (REEL_H - fg.height) // 2))
    return bg


def to_reel(src, dst, seed):
    """Still image -> 9:16 MP4 with a slow centered zoom and ambient sound."""
    from ambience import synth_audio  # numpy; only needed for images

    img = Image.open(src).convert("RGB")
    frame = dst + ".png"
    wav = dst + ".wav"
    reel_frame(img).save(frame)
    rng = random.Random(seed)
    synth_audio(wav, REEL_SECONDS, rng.choice([41.2, 49.0, 55.0, 61.7, 65.4, 73.4]), [], seed)
    frames = REEL_SECONDS * FPS
    # zoompan on a 4x upscaled frame avoids the jitter of integer crop steps
    zoom = (f"scale={REEL_W * 4}:{REEL_H * 4}:flags=lanczos,"
            f"zoompan=z='1+{ZOOM}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={REEL_W}x{REEL_H}:fps={FPS},format=yuv420p")
    subprocess.run([
        ffmpeg_exe(), "-y", "-loglevel", "error", "-i", frame, "-i", wav, "-vf", zoom,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "12M", "-bufsize", "24M",
        "-profile:v", "high", "-level", "4.1", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", str(REEL_SECONDS),
        "-movflags", "+faststart", dst,
    ], check=True)
    os.remove(frame)
    os.remove(wav)


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
    kind = "video"  # everything is posted as a reel; images are animated first
    if args.dry_run:
        print(f"kind={kind}\nsource={name}", file=sys.stdout)
        print(f"--- caption ---\n{caption}", file=sys.stderr)
        return

    os.makedirs(POSTED, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)
    stem = f"{dt.date.today():%Y%m%d}-{os.path.splitext(name)[0]}"
    if ext in IMAGES:
        media = os.path.join(BUILD, stem + ".mp4")
        to_reel(src, media, seed=sum(map(ord, name)))
        thumb = Image.open(src).convert("RGB")
        thumb.thumbnail((360, 640))
        thumb.save(os.path.join(POSTED, stem + ".jpg"), "JPEG", quality=80)
        os.remove(src)
    else:
        media = os.path.join(BUILD, stem + ext)
        shutil.move(src, media)
    txt = os.path.splitext(src)[0] + ".txt"
    if os.path.exists(txt):
        os.remove(txt)
    caption_path = os.path.join(POSTED, stem + ".txt")
    with open(caption_path, "w") as f:
        f.write(caption + "\n")

    rel = lambda p: os.path.relpath(p, os.path.dirname(HERE))  # noqa: E731
    print(f"kind={kind}\nsource={name}\nmedia={media}\ncaption={rel(caption_path)}")


if __name__ == "__main__":
    main()
