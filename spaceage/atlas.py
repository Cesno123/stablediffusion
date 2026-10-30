"""Animate a still image into a 5 second clip with Atlas Cloud (needs ATLAS_API_KEY).

animate(jpeg_bytes, key) sends the image as a base64 data URL to generateVideo,
polls the prediction every 10 seconds until data.status is "completed" (usually
2-3 minutes) and returns the MP4 bytes from data.outputs[0].
Atlas Cloud checks where requests come from: on a 403 the request is repeated
with a curl User-Agent.
"""

import base64
import os
import time

import requests

API = os.environ.get("ATLAS_API_URL", "https://api.atlascloud.ai/api/v1/model")
MODEL = os.environ.get("SPACEAGE_VIDEO_MODEL", "minimax/h3-max-turbo/image-to-video")
SECONDS = 5
RESOLUTION = "768P"
PROMPT = ("Gentle cinematic animation of this illustration: subtle natural motion of clouds, lights, vehicles "
          "and figures. Keep the original art style and texture unchanged, no new objects, no text, smooth "
          "subtle motion.")
USER_AGENT = "curl/8.5.0"


def _call(method, url, key, **kw):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.request(method, url, headers=headers, timeout=120, **kw)
    if r.status_code == 403:  # Atlas Cloud checks the origin of the request
        r = requests.request(method, url, headers={**headers, "User-Agent": USER_AGENT}, timeout=120, **kw)
    if not r.ok:
        raise RuntimeError(f"Atlas {method} {r.status_code}: {r.text[:300]}")
    return r.json()


def animate(jpeg, key, timeout=900):
    image = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()
    body = {"model": MODEL, "image": image, "duration": SECONDS, "resolution": RESOLUTION, "prompt": PROMPT}
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
