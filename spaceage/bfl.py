"""Generate images with Black Forest Labs' FLUX API (needs BFL_API_KEY).

Usage: python spaceage/bfl.py --out DIR [--count N] [--model pro|ultra] [--raw]
                              [--library [--include TITLE]]
--library draws hand-written prompts from prompt_library.py (no repeats within
a run) instead of random_prompt.py. Writes <prefix>_<n>.jpg and .txt.
"""

import argparse
import os
import random
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_library import PROMPTS  # noqa: E402
from random_prompt import make_prompt  # noqa: E402

API = os.environ.get("BFL_API_URL", "https://api.bfl.ai/v1")
MODELS = {
    # 896x1120 is 4:5, both multiples of 32
    "pro": ("flux-pro-1.1", {"width": 896, "height": 1120}),
    "ultra": ("flux-pro-1.1-ultra", {"aspect_ratio": "4:5", "raw": False}),
    # FLUX.2: 1440x1800 is 4:5 at ~2.6 MP, multiples of 16
    "flux2pro": ("flux-2-pro", {"width": 1440, "height": 1800}),
    "flux2max": ("flux-2-max", {"width": 1440, "height": 1800}),
}

# Owner's own Midjourney images, used as style references for FLUX.2
STYLE_REFS = [
    "https://raw.githubusercontent.com/Cesno123/stablediffusion/036d916cc9786e1f2c74a96bc07764614742fd90/"
    "spaceage/queue/" + name for name in (
        "u6518276545_1970s_British_science_fiction_paperback_cover_paint_74ac86b9-2952-41cc-99ad-e8fb263c07b4.png",
        "u6518276545_classic_1970s_sci-fi_paperback_art_a_gigantic_block_8ada0b14-f262-44b0-b075-5823861ff641.png",
        "u6518276545_1980s_science_fiction_cover_painting_a_sleek_red_an_9a160794-d8dc-4bf5-abce-ed1a65341bb4.png",
    )
]
STYLE_PREFIX = ("Match the painting style, brushwork, color grading and print texture of the reference "
                "images (vintage science fiction cover art), but create a completely new scene: ")


def generate(prompt, model, key, seed, raw=False, refs=()):
    endpoint, extra = MODELS[model]
    if model == "ultra":
        extra = {**extra, "raw": raw}
    body = {"prompt": prompt, "output_format": "jpeg", "seed": seed, "safety_tolerance": 2, **extra}
    for n, url in enumerate(refs, 1):  # input_image, input_image_2, ...
        body["input_image" if n == 1 else f"input_image_{n}"] = url
    headers = {"x-key": key, "accept": "application/json"}
    r = requests.post(f"{API}/{endpoint}", json=body, headers=headers, timeout=60)
    if not r.ok:
        sys.exit(f"BFL request failed {r.status_code}: {r.text}")
    job = r.json()
    poll = job.get("polling_url") or f"{API}/get_result?id={job['id']}"
    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(2)
        res = requests.get(poll, headers=headers, timeout=60).json()
        status = res.get("status")
        if status == "Ready":
            return requests.get(res["result"]["sample"], timeout=120).content
        if status not in ("Pending", "Processing", "Queued", "Task not found"):
            raise RuntimeError(f"BFL status {status}: {res}")
    raise RuntimeError("BFL timed out")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--model", choices=MODELS, default="pro")
    ap.add_argument("--prefix", default="image")
    ap.add_argument("--raw", action="store_true", help="Ultra raw mode: less polished, more natural look")
    ap.add_argument("--library", action="store_true", help="use the hand-written prompt library")
    ap.add_argument("--include", action="append", default=[], help="library title to always include")
    ap.add_argument("--style-refs", action="store_true", help="FLUX.2: use the owner's images as style references")
    args = ap.parse_args()

    key = os.environ.get("BFL_API_KEY", "").strip()
    if not key:
        sys.exit("BFL_API_KEY is not set")
    os.makedirs(args.out, exist_ok=True)
    rng = random.Random()
    if args.library:
        forced = [p for p in PROMPTS if p[0] in args.include]
        rest = [p for p in PROMPTS if p[0] not in args.include]
        jobs = (forced + rng.sample(rest, len(rest)))[:args.count]
    else:
        jobs = [("random", make_prompt(rng)[0]) for _ in range(args.count)]
    failures = 0
    for i, (title, prompt) in enumerate(jobs, 1):
        print(f"[{args.model} {i}] {title}: {prompt}", flush=True)
        try:
            refs = STYLE_REFS if args.style_refs else ()
            text = STYLE_PREFIX + prompt if args.style_refs else prompt
            data = generate(text, args.model, key, rng.randrange(2**31), args.raw, refs)
        except RuntimeError as e:  # e.g. moderated prompt: skip this one
            print(f"  skipped: {e}", flush=True)
            failures += 1
            continue
        base = os.path.join(args.out, f"{args.prefix}_{i}")
        with open(base + ".jpg", "wb") as f:
            f.write(data)
        with open(base + ".txt", "w") as f:
            f.write(f"{title}: {prompt}\n")
    if failures == len(jobs):
        sys.exit("no image could be generated")


if __name__ == "__main__":
    main()
