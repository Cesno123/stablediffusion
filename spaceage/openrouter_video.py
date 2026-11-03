"""Animate a still image into a 5 second clip through OpenRouter (needs OPENROUTER_API_KEY).

animate(jpeg_bytes, key, timeout, image_url=None) submits an image-to-video job to
POST /api/v1/videos with the picture as the first frame, polls the returned polling
URL every 10 seconds until the status is "completed" and downloads the first of the
unsigned_urls (they need the API key too). image_url: a public address of the frame;
without one the frame is sent as a base64 data URL. A 402 means the balance is empty.
The model is SPACEAGE_OPENROUTER_VIDEO_MODEL, by default Kling v3.0 Standard.
"""

import base64
import os
import time

import requests

API = os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("SPACEAGE_OPENROUTER_VIDEO_MODEL", "kwaivgi/kling-v3.0-std")
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


def animate(jpeg, key, timeout=900, image_url=None):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "SpaceAge42"}
    url = image_url or "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
    body = {
        "model": MODEL,
        "prompt": PROMPT,
        "duration": SECONDS,
        "aspect_ratio": "9:16",
        "frame_images": [{"type": "image_url", "image_url": {"url": url}, "frame_type": "first_frame"}],
    }
    job = _check(requests.post(f"{API}/videos", json=body, headers=headers, timeout=120), "submit")
    poll = job.get("polling_url") or f"{API}/videos/{job.get('id')}"
    deadline = time.time() + timeout
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
