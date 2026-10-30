"""Animate a still image into a short clip with Atlas Cloud (needs ATLAS_API_KEY).

animate(image_url, prompt, key) starts an image-to-video job (Kling O3 by default,
SPACEAGE_VIDEO_MODEL overrides it), waits for it and returns the MP4 bytes.
The image must be reachable on the internet (our server serves it from WWW).

Atlas Cloud's docs disagree on a few names (first frame "image" or "image_url",
result under data.outputs or output.video_url), so the request sends the field
the model page names and the reply is searched for the first video URL.
"""

import os
import time

import requests

API = os.environ.get("ATLAS_API_URL", "https://api.atlascloud.ai/api/v1/model")
MODEL = os.environ.get("SPACEAGE_VIDEO_MODEL", "kwaivgi/kling-video-o3-pro/image-to-video")
SECONDS = 5


def _video_url(obj):
    """First http(s) URL in a reply that looks like a video."""
    if isinstance(obj, str):
        return obj if obj.startswith("http") and ".mp4" in obj.split("?")[0].lower() else None
    if isinstance(obj, dict):
        obj = list(obj.values())
    if isinstance(obj, list):
        for v in obj:
            url = _video_url(v)
            if url:
                return url
    return None


def _status(reply):
    data = reply.get("data") if isinstance(reply.get("data"), dict) else reply
    return str(data.get("status", "")).lower(), data


def animate(image_url, prompt, key, timeout=900):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {"model": MODEL, "prompt": prompt, "image": image_url, "duration": SECONDS}
    r = requests.post(f"{API}/generateVideo", json=body, headers=headers, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Atlas request failed {r.status_code}: {r.text[:300]}")
    _, data = _status(r.json())
    job = data.get("id") or data.get("request_id") or data.get("prediction_id")
    if not job:
        raise RuntimeError(f"Atlas gave no job id: {r.text[:300]}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(5)
        res = requests.get(f"{API}/prediction/{job}", headers=headers, timeout=60)
        if res.status_code == 404:  # older API form
            res = requests.get(f"{API}/prediction/{job}/get", headers=headers, timeout=60)
        reply = res.json()
        status, data = _status(reply)
        if status in ("completed", "succeeded", "success"):
            url = _video_url(data)
            if not url:
                raise RuntimeError(f"Atlas finished without a video URL: {str(reply)[:300]}")
            return requests.get(url, timeout=300).content
        if status in ("failed", "error", "canceled", "cancelled"):
            raise RuntimeError(f"Atlas job {status}: {str(reply)[:300]}")
    raise RuntimeError("Atlas timed out")


# Camera and motion per picture mood: calm and small, so the painting stays a painting
MOTION = {
    "action": "engines flare and the ships move forward with momentum, sparks and debris drift past",
    "heroic": "a slow majestic upward camera tilt, lights glint along the hull",
    "eerie": "fog creeps slowly, faint lights flicker, something barely moves in the shadows",
    "cosmic": "stars twinkle, nebula clouds drift very slowly, the planet turns almost imperceptibly",
    "gentle": "a soft breeze moves grass and clouds, warm light shifts gently",
    "neon": "rain falls, neon lights flicker and reflect on wet ground",
    "retro": "the saucer hovers and wobbles gently, lights blink in sequence",
    "deep": "light rays shimmer through the water, particles and bubbles float slowly upward",
}


GENERIC = "lights glow and pulse softly, dust, clouds and particles drift slowly"


def motion_prompt(mood=None):
    """mood=None when it was only guessed from colors: then a motion that suits any picture."""
    return ("Bring this painting gently to life: " + MOTION.get(mood, GENERIC) + ". "
            "Slow, smooth camera push-in. Keep the exact painted style, brushwork, colors and composition; "
            "no new objects, no morphing, no text.")
