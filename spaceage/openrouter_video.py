"""Animate a still image into a 5 second clip through OpenRouter (needs OPENROUTER_API_KEY).

animate(jpeg_bytes, key, timeout, image_url=None) submits an image-to-video job to
POST /api/v1/videos with the picture as the first frame, polls the returned polling
URL every 10 seconds until the status is "completed" and downloads the first of the
unsigned_urls (they need the API key too). The frame is sent as a base64 data URL; if
that fails, image_url (a public address of the frame) is tried. A 402 means the balance
is empty.
The model is SPACEAGE_OPENROUTER_VIDEO_MODEL, by default Kling Video O1 (image-to-video,
5 or 10 seconds). If the model refuses the 9:16 aspect ratio, the request is repeated
without it; the reel is cropped to 9:16 afterwards anyway.
"""

import base64
import os
import time

import requests

API = os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("SPACEAGE_OPENROUTER_VIDEO_MODEL", "kwaivgi/kling-video-o1")
SECONDS = 5
PROMPT = ("Very slow, smooth camera push-in. The scene stays almost still: all objects keep their exact shape, "
          "rigid, no deformation; only light and atmosphere move very subtly. Preserve the original art style, "
          "fine lines, textures, colors and every detail exactly. No morphing, no new objects, no text, no flicker.")


def _check(r, what):
    if r.status_code == 402:
        raise RuntimeError("OpenRouter 402: balance empty")
    if not r.ok:
        raise RuntimeError(f"OpenRouter {what} {r.status_code}: {r.text[:300]}")
    return r.json()


def _run(body, headers, deadline):
    """Submit one job and wait for it; returns the video bytes or raises."""
    r = requests.post(f"{API}/videos", json=body, headers=headers, timeout=120)
    if r.status_code == 400 and "aspect_ratio" in body:  # e.g. a model without a 9:16 option
        body = {k: v for k, v in body.items() if k != "aspect_ratio"}
        r = requests.post(f"{API}/videos", json=body, headers=headers, timeout=120)
    job = _check(r, "submit")
    poll = job.get("polling_url") or f"{API}/videos/{job.get('id')}"
    while time.time() < deadline:
        time.sleep(10)
        state = _check(requests.get(poll, headers=headers, timeout=60), "poll")
        status = str(state.get("status", "")).lower()
        if status == "completed":
            urls = state.get("unsigned_urls") or []
            if not urls:
                raise RuntimeError(f"OpenRouter finished without a video URL: {str(state)[:300]}")
            video = requests.get(urls[0], headers=headers, timeout=300)
            video.raise_for_status()
            return video.content
        if status in ("failed", "cancelled", "canceled", "expired"):
            raise RuntimeError(f"OpenRouter job {status}: {str(state.get('error') or state)[:300]}")
    raise RuntimeError("OpenRouter timed out")


def animate(jpeg, key, timeout=900, image_url=None, model=None, prompt=None):
    """The frame goes in as base64 first: some providers (Kling via AtlasCloud) cannot fetch it
    from our server. If that fails, the public image_url is tried. Failed jobs cost nothing."""
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "SpaceAge42"}
    sources = ["data:image/jpeg;base64," + base64.b64encode(jpeg).decode()] + ([image_url] if image_url else [])
    deadline = time.time() + timeout
    error = None
    for url in sources:
        body = {
            "model": model or MODEL,
            "prompt": prompt or PROMPT,
            "duration": SECONDS,
            "aspect_ratio": "9:16",
            "frame_images": [{"type": "image_url", "image_url": {"url": url}, "frame_type": "first_frame"}],
        }
        try:
            return _run(body, headers, deadline)
        except RuntimeError as e:
            if "402" in str(e) or "timed out" in str(e):
                raise
            error = e
    raise error
