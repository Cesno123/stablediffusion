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
}


def generate(prompt, model, key, seed, raw=False):
    endpoint, extra = MODELS[model]
    if model == "ultra":
        extra = {**extra, "raw": raw}
    body = {"prompt": prompt, "output_format": "jpeg", "seed": seed, "safety_tolerance": 2, **extra}
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
            data = generate(prompt, args.model, key, rng.randrange(2**31), args.raw)
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
