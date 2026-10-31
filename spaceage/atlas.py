"""Animate a still image into a 5 second clip with Atlas Cloud (needs ATLAS_API_KEY).

animate(jpeg_bytes, key) sends the image as a base64 data URL to generateVideo,
polls the prediction every 10 seconds until data.status is "completed" (a few
minutes) and returns the MP4 bytes from data.outputs[0].
Atlas Cloud checks where requests come from, so every request carries a curl
User-Agent. A 402 means the Atlas balance is empty.
"""

import base64
import os
import time

import requests

API = os.environ.get("ATLAS_API_URL", "https://api.atlascloud.ai/api/v1/model")
MODEL = os.environ.get("SPACEAGE_VIDEO_MODEL", "kwaivgi/kling-v3.0-pro/image-to-video")
SECONDS = 5
PROMPT = ("Very slow, smooth camera push-in. The scene stays almost still: all objects keep their exact shape, "
          "rigid, no deformation; only light and atmosphere move very subtly. Preserve the original art style, "
          "fine lines, textures, colors and every detail exactly. No morphing, no new objects, no text, no flicker.")
USER_AGENT = "curl/8.5.0"


def _call(method, url, key, **kw):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": USER_AGENT}
    r = requests.request(method, url, headers=headers, timeout=120, **kw)
    if r.status_code == 402:
        raise RuntimeError("Atlas 402: balance empty")
    if not r.ok:
        raise RuntimeError(f"Atlas {method} {r.status_code}: {r.text[:300]}")
    return r.json()


def animate(jpeg, key, timeout=900):
    image = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
    body = {"model": MODEL, "image": image, "duration": SECONDS, "sound": False, "prompt": PROMPT}
    reply = _call("POST", f"{API}/generateVideo", key, json=body)
    job = (reply.get("data") or {}).get("id")
    if not job:
        raise RuntimeError(f"Atlas gave no prediction id: {str(reply)[:300]}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(10)
        data = _call("GET", f"{API}/prediction/{job}", key).get("data") or {}
        status = str(data.get("status", "")).lower()
        if status == "completed":
            outputs = data.get("outputs") or []
            if not outputs:
                raise RuntimeError(f"Atlas finished without outputs: {str(data)[:300]}")
            video = requests.get(outputs[0], headers={"User-Agent": USER_AGENT}, timeout=300)
            video.raise_for_status()
            return video.content
        if status in ("failed", "error", "canceled", "cancelled"):
            raise RuntimeError(f"Atlas job {status}: {str(data.get('error') or data)[:300]}")
    raise RuntimeError("Atlas timed out")
