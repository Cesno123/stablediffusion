"""Generate the next post image when the queue is empty.

Picks a random prompt from prompt_library.py that has not been used yet
(posted/used_prompts.txt; starts over once all are used), renders it with
FLUX.2 [max] and saves it to queue/ for post_queue.py. Needs BFL_API_KEY.
"""

import datetime as dt
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bfl import generate  # noqa: E402
from post_queue import IMAGES, VIDEOS, QUEUE  # noqa: E402
from prompt_library import PROMPTS  # noqa: E402

USED = os.path.join(HERE, "posted", "used_prompts.txt")
MODEL = os.environ.get("SPACEAGE_MODEL", "flux2max")


def queue_has_media():
    return any(os.path.splitext(f)[1].lower() in IMAGES | VIDEOS for f in os.listdir(QUEUE))


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
    fresh = [p for p in PROMPTS if p[0] not in used]
    if not fresh:  # every prompt used once: start a new round
        used, fresh = set(), list(PROMPTS)
        open(USED, "w").close()
    rng = random.Random()
    for title, prompt in rng.sample(fresh, min(3, len(fresh))):  # retry with another prompt on failure
        print(f"generating '{title}' with {MODEL}", flush=True)
        try:
            data = generate(prompt, MODEL, key, rng.randrange(2**31))
        except RuntimeError as e:
            print(f"  failed: {e}", flush=True)
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        path = os.path.join(QUEUE, f"auto-{dt.datetime.utcnow():%Y%m%d-%H%M}-{slug}.jpg")
        with open(path, "wb") as f:
            f.write(data)
        os.makedirs(os.path.dirname(USED), exist_ok=True)
        with open(USED, "a") as f:
            f.write(title + "\n")
        print(f"saved {os.path.relpath(path, HERE)}")
        return
    sys.exit("no image could be generated")


if __name__ == "__main__":
    main()
