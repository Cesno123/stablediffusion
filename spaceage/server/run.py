"""One posting round on the own server (replaces the GitHub workflow).

Started by cron 4 times a day (9:07, 13:07, 18:07, 21:07):
  1. queue empty -> generate a new FLUX image (autogen.py)
  2. turn a random queued image (or a waiting video) into a 9:16 reel with zoom and sound;
     the 5th, 15th, 25th, ... post is a 5 second Atlas Cloud clip instead (ATLAS_API_KEY), made by a
     --prepare run 15 minutes earlier; if that failed, the image is posted
  3. put the reel into the public web folder (served by Caddy) and let
     Instagram fetch it from there
  4. only after a successful post: remove the original from the queue,
     keep a small preview in posted/

Settings come from /etc/spaceage.env (see install.sh). The Instagram token
is renewed automatically every 20 days and kept in DATA/ig_token.txt.
The result of the last round is written to WWW/status.txt.
"""

import argparse
import html
import datetime as dt
import json
import os
import random
import re
import shutil
import sys
import time
import traceback
import zlib

import requests
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import autogen  # noqa: E402
import post_instagram as ig  # noqa: E402
import post_queue as pq  # noqa: E402
import tiktok  # noqa: E402

DATA = os.environ.get("SPACEAGE_DATA", "/var/lib/spaceage")
WWW = os.environ.get("SPACEAGE_WWW", "/srv/spaceage/www")
PUBLIC_URL = os.environ.get("SPACEAGE_PUBLIC_URL", "").rstrip("/")
TOKEN_FILE = os.path.join(DATA, "ig_token.txt")
PREPARED_MP4 = os.path.join(DATA, "prepared.mp4")  # Atlas clip made ahead of its post
PREPARED_INFO = os.path.join(DATA, "prepared.json")
REFRESH_DAYS = 20


def log(msg):
    print(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def write_status(text):
    os.makedirs(WWW, exist_ok=True)
    with open(os.path.join(WWW, "status.txt"), "w") as f:
        f.write(f"{dt.datetime.now():%d.%m.%Y %H:%M} {text}\n")


def ig_token():
    """Current token; renewed (valid 60 days) once it is REFRESH_DAYS old."""
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token = f.read().strip() or token
        age = time.time() - os.path.getmtime(TOKEN_FILE)
    else:
        age = REFRESH_DAYS * 86400  # first run: renew right away
    if not token:
        sys.exit("IG_ACCESS_TOKEN is not set in /etc/spaceage.env")
    if age >= REFRESH_DAYS * 86400:
        r = requests.get("https://graph.instagram.com/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=60)
        if r.ok:
            token = r.json()["access_token"]
            log("Instagram token renewed")
        else:  # e.g. token younger than 24 h: keep it, try again next round
            log(f"token renewal skipped: {r.status_code} {r.text}")
            if os.path.exists(TOKEN_FILE):
                return token
        os.makedirs(DATA, exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        os.chmod(TOKEN_FILE, 0o600)
    return token


def ig_user_id(token):
    uid = os.environ.get("IG_USER_ID", "").strip()
    if uid:
        return uid
    info = ig.check(requests.get(f"{ig.GRAPH}/me", params={"fields": "user_id,username", "access_token": token},
                                 timeout=60))
    return str(info.get("user_id") or info["id"])


def drop_prepared():
    for path in (PREPARED_MP4, PREPARED_INFO):
        if os.path.exists(path):
            os.remove(path)


def prepared_src():
    """Queue file whose Atlas clip was prepared for exactly the coming post, else None (stale ones are dropped)."""
    try:
        with open(PREPARED_INFO) as f:
            info = json.load(f)
    except (OSError, ValueError):
        return None
    src = os.path.join(pq.QUEUE, os.path.basename(info.get("src", "")))
    if info.get("post") == pq.posts_so_far() + 1 and os.path.isfile(src) and os.path.isfile(PREPARED_MP4):
        return src
    drop_prepared()
    return None


def prepare():
    """Run 15 minutes before a post: when that post is the 5th, 15th, 25th, ... animate an image now
    (it takes a few minutes), so the post can use the finished clip. Atlas Cloud (ATLAS_API_KEY) is
    tried first, so its prepaid balance gets used; when it fails or is empty, OpenRouter
    (OPENROUTER_API_KEY). If both fail, the post stays a picture."""
    number = pq.posts_so_far() + 1
    providers = [(name, os.environ.get(var, "").strip(), label) for name, var, label in
                 (("atlas", "ATLAS_API_KEY", "Atlas"), ("openrouter", "OPENROUTER_API_KEY", "OpenRouter"))]
    providers = [p for p in providers if p[1]]
    if number % pq.ANIMATE_EVERY != pq.ANIMATE_AT:
        return f"Vorbereitung: Post Nr. {number} wird kein Video"
    if not providers:
        return "Vorbereitung: weder ATLAS_API_KEY noch OPENROUTER_API_KEY, Post bleibt ein Bild"
    if pq.video_turn():
        return "Vorbereitung: ein eigenes Video ist dran"
    if prepared_src():
        return "Vorbereitung: Video liegt schon bereit"
    images = pq.queue_files(pq.IMAGES)
    if not images:
        return "Vorbereitung: keine Bilder in der Warteschlange"
    src = random.choice(images)
    name = os.path.basename(src)
    os.makedirs(DATA, exist_ok=True)
    public = (WWW, PUBLIC_URL) if PUBLIC_URL and os.path.isdir(WWW) else None
    deadline = time.time() + 780  # the post follows 15 minutes after this run
    failures = []
    for provider, key, label in providers:
        left = int(deadline - time.time())
        if left < 120:
            break
        try:
            pq.to_moving_reel(src, PREPARED_MP4, zlib.crc32(name.encode()), key, timeout=left,
                              provider=provider, public=public)
        except Exception as e:  # noqa: BLE001 - e.g. 402 balance empty: try the next provider
            drop_prepared()
            failures.append(f"{label}: {e}")
            continue
        with open(PREPARED_INFO, "w") as f:
            json.dump({"src": name, "post": number}, f)
        done = f"Vorbereitung: {label}-Video aus {name} fertig fuer Post Nr. {number}"
        return done + (f" ({'; '.join(failures)})" if failures else "")
    return f"Vorbereitung: Video fehlgeschlagen ({'; '.join(failures) or 'keine Zeit mehr'}), Post bleibt ein Bild"

TEST_MODELS = "kwaivgi/kling-video-o1,kwaivgi/kling-v3.0-std"


def test_index():
    """WWW/tests/index.html: every test clip as a player, newest first, so one link shows them all."""
    import html as _html

    folder = os.path.join(WWW, "tests")
    os.makedirs(folder, exist_ok=True)
    clips = sorted((f for f in os.listdir(folder) if f.endswith(".mp4")), reverse=True)
    items = "".join(
        f'<p>{_html.escape(f[:15])} &middot; <b>{_html.escape(f[16:-4])}</b></p>'
        f'<video src="{_html.escape(f)}" controls playsinline loop preload="metadata" '
        f'style="width:100%;max-width:420px"></video>' for f in clips)
    page = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>SpaceAge Video-Tests</title><body style="font-family:sans-serif;background:#111;color:#eee;'
            f'padding:16px;max-width:460px;margin:auto"><h2>Video-Tests</h2>{items or "<p>Noch keine Tests.</p>"}')
    with open(os.path.join(folder, "index.html"), "w") as f:
        f.write(page)
    return f"Test-Seite: {PUBLIC_URL}/tests/ ({len(clips)} Videos)"


def test_videos(image=None, models=TEST_MODELS, prompts=None):
    """Animate one queued image with several OpenRouter models for comparison. Nothing is posted,
    nothing leaves the queue, the post counter stays; the clips land in WWW/tests/ for the phone."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return "Test: kein OPENROUTER_API_KEY"
    if image:
        src = os.path.join(pq.QUEUE, os.path.basename(image))
        if not os.path.isfile(src):
            return f"Test: {image} liegt nicht in der Warteschlange"
    else:
        images = pq.queue_files(pq.IMAGES)
        if not images:
            return "Test: keine Bilder in der Warteschlange"
        src = random.choice(images)
    name = os.path.basename(src)
    folder = os.path.join(WWW, "tests")
    os.makedirs(folder, exist_ok=True)
    stamp = f"{dt.datetime.now():%Y%m%d-%H%M%S}"
    lines = [f"Test mit {name}:"]
    texts = [p.strip() for p in (prompts or "").split("|") if p.strip()] or [None]  # None = the usual prompt
    for model in [m.strip() for m in models.split(",") if m.strip()]:
        for k, text in enumerate(texts, 1):
            tag = f"-p{k}" if len(texts) > 1 else ""
            out = f"{stamp}-{model.split('/')[-1]}{tag}.mp4"
            label = f"{model}{f' (Prompt {k})' if tag else ''}"
            try:
                pq.to_moving_reel(src, os.path.join(folder, out), zlib.crc32(name.encode()), key, timeout=900,
                                  provider="openrouter", public=(WWW, PUBLIC_URL) if PUBLIC_URL else None,
                                  model=model, prompt=text)
                lines.append(f"  {label}: {PUBLIC_URL}/tests/{out}")
            except Exception as e:  # noqa: BLE001 - one failing model must not stop the others
                lines.append(f"  {label}: fehlgeschlagen ({e})")
    lines.append(test_index())
    return "\n".join(lines)


def post_next(dry_run=False):
    if os.environ.get("BFL_API_KEY", "").strip():
        try:
            autogen.main()
        except SystemExit as e:  # no image this round; maybe the queue still has something
            log(f"FLUX: {e}")
    prepared = prepared_src()
    src = prepared or pq.next_file()
    if not src:
        return "Warteschlange leer, nichts gepostet"
    name = os.path.basename(src)
    ext = os.path.splitext(name)[1].lower()
    caption = pq.caption_for(src)

    os.makedirs(WWW, exist_ok=True)
    for old in os.listdir(WWW):  # only the current reel stays public
        if old.endswith(".mp4"):
            os.remove(os.path.join(WWW, old))
    reel = f"reel-{dt.datetime.now():%Y%m%d-%H%M%S}.mp4"
    media = os.path.join(WWW, reel)
    log(f"building reel from {name}")
    if prepared:  # the Atlas clip made 15 minutes ago for this post
        shutil.copyfile(PREPARED_MP4, media)
        log("posting the video prepared for this post")
    elif ext in pq.IMAGES:
        pq.to_reel(src, media, seed=zlib.crc32(name.encode()))
    else:  # an uploaded video; a silent one gets music for its mood
        log(f"video: {pq.video_with_sound(src, media, zlib.crc32(name.encode()))}")
    if dry_run:
        return f"Probelauf: {name} -> {PUBLIC_URL}/{reel} (nicht gepostet)"
    if not PUBLIC_URL:
        sys.exit("SPACEAGE_PUBLIC_URL is not set")

    token = ig_token()
    user_id = ig_user_id(token)
    container = ig.create_container(user_id, token, caption, f"{PUBLIC_URL}/{reel}")
    ig.wait_until_ready(container, token)
    media_id = ig.publish(user_id, token, container)
    pq.count_post()
    if tiktok.enabled():
        try:
            log(tiktok.post(media, caption))
        except Exception as e:  # TikTok must never break the Instagram post
            log(f"TikTok fehlgeschlagen: {type(e).__name__}: {e}")
    try:
        tiktok_keep(media, caption)
    except Exception as e:  # the TikTok page must never break a post
        log(f"tiktok page: {type(e).__name__}: {e}")

    # posted: archive a small preview and the caption, drop the original
    os.makedirs(pq.POSTED, exist_ok=True)
    stem = f"{dt.date.today():%Y%m%d}-{os.path.splitext(name)[0]}"
    if ext in pq.IMAGES:
        thumb = Image.open(src).convert("RGB")
        thumb.thumbnail((360, 640))
        thumb.save(os.path.join(pq.POSTED, stem + ".jpg"), "JPEG", quality=80)
    with open(os.path.join(pq.POSTED, stem + ".txt"), "w") as f:
        f.write(caption + "\n")
    os.remove(src)
    txt = os.path.splitext(src)[0] + ".txt"
    if os.path.exists(txt):
        os.remove(txt)
    drop_prepared()
    return f"gepostet: {name} (Instagram-ID {media_id})" + (" als Video" if prepared else "")


TIKTOK_KEEP = 10
TIKTOK_PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SpaceAge42 f&uuml;r TikTok</title>
<body style="font-family:sans-serif;background:#111;color:#eee;padding:16px;max-width:640px;margin:auto">
<h2>F&uuml;r TikTok</h2>
<p style="font-size:14px">Die letzten {n} Reels, die auf Instagram gegangen sind, neueste oben.
1. Herunterladen &nbsp;2. Text kopieren &nbsp;3. In TikTok posten, Schalter <b>KI-generierter Inhalt</b> an
&nbsp;4. Hier abhaken (merkt sich nur dieses Handy).</p>
{items}
<script>
const done = JSON.parse(localStorage.getItem("tt") || "[]");
document.querySelectorAll("input[data-r]").forEach(b => {{
  b.checked = done.includes(b.dataset.r);
  b.closest("div.r").style.opacity = b.checked ? .4 : 1;
  b.onchange = () => {{
    const s = new Set(JSON.parse(localStorage.getItem("tt") || "[]"));
    b.checked ? s.add(b.dataset.r) : s.delete(b.dataset.r);
    localStorage.setItem("tt", JSON.stringify([...s]));
    b.closest("div.r").style.opacity = b.checked ? .4 : 1;
  }};
}});
function copy(id, btn) {{
  navigator.clipboard.writeText(document.getElementById(id).value);
  btn.textContent = "kopiert";
}}
</script>"""
TIKTOK_ITEM = """<div class="r" style="border-top:1px solid #333;padding:12px 0">
<video src="{reel}" controls playsinline preload="metadata" style="width:100%;max-height:70vh;background:#000"></video>
<p><a href="{reel}" download style="color:#9cf;font-size:18px">Herunterladen</a> &nbsp; <small>{when}</small></p>
<textarea id="c{i}" rows="5" style="width:100%">{caption}</textarea>
<p><button onclick="copy('c{i}', this)" style="font-size:16px">Text kopieren</button>
&nbsp; <label><input type="checkbox" data-r="{reel}"> auf TikTok gepostet</label></p></div>"""


def tiktok_keep(media, caption):
    """Keep a copy of each posted reel in WWW/tiktok/ (last TIKTOK_KEEP) and rebuild its page:
    one link to download each reel and copy its caption for posting on TikTok by hand."""
    folder = os.path.join(WWW, "tiktok")
    os.makedirs(folder, exist_ok=True)
    name = os.path.basename(media)
    shutil.copyfile(media, os.path.join(folder, name))
    with open(os.path.join(folder, name[:-4] + ".txt"), "w") as f:
        f.write(caption.strip() + "\n")
    reels = sorted((f for f in os.listdir(folder) if f.endswith(".mp4")), reverse=True)
    for old in reels[TIKTOK_KEEP:]:
        for ext in (".mp4", ".txt"):
            path = os.path.join(folder, old[:-4] + ext)
            if os.path.exists(path):
                os.remove(path)
    items = []
    for i, reel in enumerate(reels[:TIKTOK_KEEP]):
        txt = os.path.join(folder, reel[:-4] + ".txt")
        text = open(txt).read().strip() if os.path.exists(txt) else ""
        m = re.match(r"reel-(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)", reel)
        when = f"{m[3]}.{m[2]}. {m[4]}:{m[5]} Uhr" if m else ""
        items.append(TIKTOK_ITEM.format(reel=html.escape(reel), when=when, caption=html.escape(text), i=i))
    with open(os.path.join(folder, "index.html"), "w") as f:
        f.write(TIKTOK_PAGE.format(n=len(items), items="".join(items) or "<p>noch keine</p>"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="build the reel but do not post")
    ap.add_argument("--check", action="store_true", help="only test the Instagram access")
    ap.add_argument("--prepare", action="store_true", help="make the Atlas clip for the coming post if it is due")
    ap.add_argument("--test-video", action="store_true", help="compare video models on one image; posts nothing")
    ap.add_argument("--image", help="queue file for --test-video (default: a random one)")
    ap.add_argument("--models", default=TEST_MODELS, help="comma separated OpenRouter models for --test-video")
    ap.add_argument("--prompts", help="for --test-video: motion prompts separated by | (each model gets each)")
    ap.add_argument("--test-index", action="store_true", help="only rebuild the page listing the test clips")
    ap.add_argument("--flux", type=int, metavar="N", help="generate N FLUX images into the queue now")
    ap.add_argument("--set", default="comic", choices=["comic", "fifties", "library"], help="prompts for --flux")
    args = ap.parse_args()
    if args.prepare:
        log(prepare())
        return
    if args.test_video:
        log(test_videos(args.image, args.models, args.prompts))
        return
    if args.test_index:
        log(test_index())
        return
    if args.flux:
        log(autogen.batch(args.flux, args.set))
        return
    try:
        if args.check:
            token = ig_token()
            result = f"Instagram-Zugang ok (Konto-ID {ig_user_id(token)})"
        else:
            result = post_next(args.dry_run)
    except SystemExit as e:
        result = f"FEHLER: {e}"
    except Exception:  # noqa: BLE001 - every failure must end up in status.txt
        result = "FEHLER: " + traceback.format_exc(limit=3).strip().splitlines()[-1]
        traceback.print_exc()
    log(result)
    write_status(result)
    if result.startswith("FEHLER"):
        sys.exit(1)


if __name__ == "__main__":
    main()
