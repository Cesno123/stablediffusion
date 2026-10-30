"""Take the next file from spaceage/queue/ and prepare it for posting.

Images (png/jpg/webp) become a 9:16 reel (other ratios shown whole on a
blurred backdrop) with a slow 8-second zoom and a short generated piece of
music (music.py) that fits the picture's mood (mood.py). Videos (mp4/mov) are posted as reels unchanged.
Images are picked at random from the queue, so styles and upload batches mix; uploaded
videos wait and come every 10th post (VIDEO_EVERY), or earlier when no image is left.

Caption: queue/<name>.txt if it exists, otherwise default_caption() (rotating
intro and hashtags).
The reel is built in a temp folder (not committed, to keep the repo small);
posted/ only keeps a small preview image and the caption.
Prints key=value lines for $GITHUB_OUTPUT.
"""

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import zlib

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue")
POSTED = os.path.join(HERE, "posted")
BUILD = os.path.join(os.environ.get("RUNNER_TEMP", "/tmp"), "spaceage")
IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEOS = {".mp4", ".mov"}

# Caption when no queue/<name>.txt exists: one of several intros (the owner's
# text first) plus a few hashtags drawn from the pool. The same text and the
# same 30 hashtags on every post look like spam to Instagram; brand tags
# (#NASA, #SpaceX, #StarWars...) that don't match the picture were dropped.
INTROS = [
    "🚀 Step into the future with SpaceAge42 – your gateway to cosmic art and sci-fi "
    "visions! 🌌 Perfect for dreamers, explorers, and tech lovers. From interstellar "
    "landscapes to futuristic worlds, our gallery brings the thrill of space exploration "
    "to life. ✨",
    "🌌 Another world from the SpaceAge42 archive – painted like the old paperback covers "
    "we used to stare at for hours. Where would you land? 🚀",
    "✨ Giant machines, strange skies, tiny travellers. A new vision from SpaceAge42 – "
    "the future as the 70s and 80s dreamed it. 🪐",
    "🛸 Somewhere out there, this is just an ordinary day. SpaceAge42 – cosmic art and "
    "retro sci-fi for dreamers and explorers. 🌠",
    "🪐 Look closer: every hull plate, every distant moon tells a story. Welcome to "
    "SpaceAge42, a gallery of worlds that never were – yet. 🚀",
    "🌠 Turn the volume up, let the picture pull you in. SpaceAge42 – interstellar "
    "landscapes and futuristic worlds, one transmission at a time. 📡",
    "🚀 Ready for departure? SpaceAge42 brings you sci-fi art inspired by the golden age "
    "of space paintings – for everyone who still looks up at night. 🌌",
    "🌌 A postcard from the far future. Which detail do you spot first? SpaceAge42 – "
    "cosmic art and sci-fi visions. ✨",
]
HASHTAGS = (
    "#SciFiArt #SpaceArt #FuturisticVibes #CosmicDreams #ExploreTheUniverse #DigitalArt "
    "#FutureWorlds #SciFiCommunity #AstronomyLovers #GalaxyVibes #StarsAndBeyond #NewWorlds "
    "#DeepSpaceDreams #SciFiUniverse #SpaceExploration #OuterSpaceArt #StellarVisions "
    "#NextFrontier #MarsMission #space #astronomy #dystopian #RetroSciFi #RetroFuturism "
    "#SciFiIllustration #SpaceshipArt #PulpArt #ConceptArt"
).split()
TAGS_PER_POST = 7  # #SpaceAge42 plus 6 from the pool


def default_caption(src):
    """Intro and hashtags for one file; the same file always gets the same caption."""
    import hashlib
    import random

    rng = random.Random(hashlib.sha256(os.path.basename(src).encode()).hexdigest())
    tags = ["#SpaceAge42"] + rng.sample(HASHTAGS, TAGS_PER_POST - 1)
    return rng.choice(INTROS) + "\n\n" + " ".join(tags)


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


VIDEO_EVERY = 10  # every 10th post is a video from the queue (when one is waiting)
POST_COUNT = os.path.join(POSTED, "post_count.txt")


def queue_files(kinds):
    """Queue files with one of these extensions, oldest upload first."""
    if not os.path.isdir(QUEUE):
        return []
    files = [os.path.join(QUEUE, f) for f in os.listdir(QUEUE) if os.path.splitext(f)[1].lower() in kinds]
    return sorted(files, key=lambda p: (added_at(p), p))


def posts_so_far():
    try:
        with open(POST_COUNT) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def count_post():
    count = posts_so_far() + 1  # read before "w" empties the file
    os.makedirs(POSTED, exist_ok=True)
    with open(POST_COUNT, "w") as f:
        f.write(f"{count}\n")


def video_turn():
    """True when the next post is the 10th, 20th, ... and a video is waiting."""
    return (posts_so_far() + 1) % VIDEO_EVERY == 0 and bool(queue_files(VIDEOS))


def next_file():
    """A random image (mixes styles and upload batches); the oldest waiting video every
    VIDEO_EVERY posts (or when no image is left)."""
    import random

    images, videos = queue_files(IMAGES), queue_files(VIDEOS)
    if videos and (video_turn() or not images):
        return videos[0]
    return random.choice(images) if images else None


def caption_for(src):
    txt = os.path.splitext(src)[0] + ".txt"
    if os.path.exists(txt):
        with open(txt) as f:
            return f.read().strip()
    return default_caption(src)


REEL_W, REEL_H, REEL_SECONDS, FPS = 1080, 1920, 8, 30


def ffmpeg_exe():
    """Bundled ffmpeg from imageio-ffmpeg (no apt needed), else the system one."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):  # e.g. no bundled binary for Arm
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
    from music import pick  # numpy; only needed for images

    img = Image.open(src).convert("RGB")
    frame = dst + ".png"
    wav = dst + ".wav"
    reel_frame(img).save(frame)
    from mood import mood_of

    own = os.path.splitext(src)[0] + ".txt"  # only the owner's own text says something about this picture
    mood, why = mood_of(src, caption_for(src) if os.path.exists(own) else "")
    print(f"mood: {mood} ({why})", file=sys.stderr, flush=True)
    print(f"music: {pick(wav, REEL_SECONDS, seed, os.path.join(POSTED, 'used_sounds.txt'), mood)}", file=sys.stderr, flush=True)
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


def to_moving_reel(src, dst, seed, key):
    """Still image -> 5 second clip animated by Atlas Cloud, with our music for its mood."""
    import io

    import atlas
    from mood import mood_of
    from music import pick

    buf = io.BytesIO()
    reel_frame(Image.open(src).convert("RGB")).save(buf, "JPEG", quality=90)
    wav = dst + ".wav"
    clip = dst + ".clip.mp4"
    try:
        own = os.path.splitext(src)[0] + ".txt"
        mood, why = mood_of(src, caption_for(src) if os.path.exists(own) else "")
        print(f"mood: {mood} ({why})", file=sys.stderr, flush=True)
        print(f"music: {pick(wav, atlas.SECONDS, seed, os.path.join(POSTED, 'used_sounds.txt'), mood)}",
              file=sys.stderr, flush=True)
        with open(clip, "wb") as f:
            f.write(atlas.animate(buf.getvalue(), key))
        fit = (f"scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=increase:flags=lanczos,"
               f"crop={REEL_W}:{REEL_H},fps={FPS},format=yuv420p")
        subprocess.run([
            ffmpeg_exe(), "-y", "-loglevel", "error", "-i", clip, "-i", wav, "-map", "0:v:0", "-map", "1:a:0",
            "-vf", fit, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "12M",
            "-bufsize", "24M", "-profile:v", "high", "-level", "4.1",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", str(atlas.SECONDS), "-shortest",
            "-movflags", "+faststart", dst,
        ], check=True)
    finally:
        for tmp in (wav, clip):
            if os.path.exists(tmp):
                os.remove(tmp)


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
        to_reel(src, media, seed=zlib.crc32(name.encode()))
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
