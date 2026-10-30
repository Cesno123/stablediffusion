"""One posting round on the own server (replaces the GitHub workflow).

Started by cron every four hours (4 times a day):
  1. queue empty -> generate a new FLUX image (autogen.py)
  2. turn the oldest queue file into a 9:16 reel with zoom and sound
  3. put the reel into the public web folder (served by Caddy) and let
     Instagram fetch it from there
  4. only after a successful post: remove the original from the queue,
     keep a small preview in posted/

Settings come from /etc/spaceage.env (see install.sh). The Instagram token
is renewed automatically every 20 days and kept in DATA/ig_token.txt.
The result of the last round is written to WWW/status.txt.
"""

import argparse
import datetime as dt
import os
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

DATA = os.environ.get("SPACEAGE_DATA", "/var/lib/spaceage")
WWW = os.environ.get("SPACEAGE_WWW", "/srv/spaceage/www")
PUBLIC_URL = os.environ.get("SPACEAGE_PUBLIC_URL", "").rstrip("/")
TOKEN_FILE = os.path.join(DATA, "ig_token.txt")
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


def post_next(dry_run=False):
    if os.environ.get("BFL_API_KEY", "").strip():
        try:
            autogen.main()
        except SystemExit as e:  # no image this round; maybe the queue still has something
            log(f"FLUX: {e}")
    src = pq.next_file()
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
    if ext in pq.IMAGES:
        pq.to_reel(src, media, seed=zlib.crc32(name.encode()))
    else:
        with open(src, "rb") as fi, open(media, "wb") as fo:
            fo.write(fi.read())
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
    return f"gepostet: {name} (Instagram-ID {media_id})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="build the reel but do not post")
    ap.add_argument("--check", action="store_true", help="only test the Instagram access")
    args = ap.parse_args()
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
