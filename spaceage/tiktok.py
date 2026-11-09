"""Post a finished reel to TikTok through Upload-Post (needs UPLOAD_POST_API_KEY and UPLOAD_POST_USER).

TikTok only lets audited apps for many users post publicly, so a private server cannot do it
directly. Upload-Post runs such an approved app; the TikTok account is connected once in its
dashboard (a "profile", whose name goes into UPLOAD_POST_USER). TikTok posting needs a paid
Upload-Post plan (Basic and up); the Free plan answers 403.

post(path, caption) sends the video file to POST https://api.upload-post.com/api/upload with
platform[]=tiktok, public, labelled as AI-generated (is_aigc), and async_upload=true so the
call returns at once with a request_id while Upload-Post publishes in the background.
Reference: https://docs.upload-post.com/api/upload-video
"""

import os

import requests

API = "https://api.upload-post.com/api/upload"


def enabled():
    return bool(os.environ.get("UPLOAD_POST_API_KEY", "").strip() and os.environ.get("UPLOAD_POST_USER", "").strip())


def post(path, caption):
    """Returns a short report line; raises RuntimeError on a refused upload."""
    key = os.environ.get("UPLOAD_POST_API_KEY", "").strip()
    user = os.environ.get("UPLOAD_POST_USER", "").strip()
    if not (key and user):
        return "TikTok: aus (UPLOAD_POST_API_KEY oder UPLOAD_POST_USER fehlt)"
    data = {
        "user": user,
        "platform[]": "tiktok",
        "title": caption[:2200],
        "tiktok_title": caption[:2200],
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "is_aigc": "true",
        "async_upload": "true",
    }
    with open(path, "rb") as f:
        r = requests.post(API, headers={"Authorization": f"Apikey {key}"}, data=data,
                          files={"video": (os.path.basename(path), f, "video/mp4")}, timeout=300)
    try:
        body = r.json()
    except ValueError:
        body = {"message": r.text[:200]}
    if not r.ok or body.get("success") is False:
        raise RuntimeError(f"TikTok {r.status_code}: {str(body.get('message') or body.get('error') or body)[:200]}")
    return f"TikTok: angenommen (request_id {body.get('request_id', '?')})"
