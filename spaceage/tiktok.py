"""Post a finished reel to TikTok through Zernio (needs ZERNIO_API_KEY).

TikTok only lets audited apps for many users post publicly, so a private server cannot do it
directly. Zernio runs such an app; the TikTok account is connected once in its dashboard.
Zernio's first two connected accounts are free.

post(video_url, caption) calls POST https://zernio.com/api/v1/posts with the reel's public URL
in mediaItems, the TikTok account, tiktokSettings (public, AI-generated disclosure and the two
consent flags TikTok requires on every post) and publishNow. Only TikTok is posted here:
Instagram is posted by the server itself.
The TikTok account id comes from ZERNIO_TIKTOK_ACCOUNT, or else from GET /v1/accounts?platform=tiktok.
Docs: https://docs.zernio.com/platforms/tiktok.mdx and https://docs.zernio.com/posts/create-post.mdx
"""

import os

import requests

API = "https://zernio.com/api/v1"


def _key():
    return os.environ.get("ZERNIO_API_KEY", "").strip()


def enabled():
    return bool(_key())


def _headers():
    return {"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"}


def _check(r, what):
    try:
        body = r.json()
    except ValueError:
        body = {"error": r.text[:200]}
    if not r.ok:
        raise RuntimeError(f"Zernio {what} {r.status_code}: {str(body.get('error') or body)[:200]}")
    return body


def accounts():
    """[(id, username, status)] of the connected TikTok accounts."""
    body = _check(requests.get(f"{API}/accounts", headers=_headers(), params={"platform": "tiktok"}, timeout=60),
                  "accounts")
    return [(a.get("_id") or a.get("id"), a.get("username") or a.get("displayName"), a.get("status"))
            for a in body.get("accounts", [])]


def account_id():
    fixed = os.environ.get("ZERNIO_TIKTOK_ACCOUNT", "").strip()
    if fixed:
        return fixed
    found = [a for a in accounts() if a[0]]
    if not found:
        raise RuntimeError("Zernio: kein TikTok-Konto verbunden")
    return found[0][0]


class AlreadyPosted(RuntimeError):
    """Zernio 409: this exact video was scheduled or posted on the account within 24 hours."""


def post(video_url, caption, when=None):
    """Publish now, or at `when` (a UTC datetime) through Zernio's scheduledFor.
    Returns a short report line; raises AlreadyPosted on a duplicate, RuntimeError on any other refusal."""
    if not enabled():
        return "TikTok: aus (ZERNIO_API_KEY fehlt)"
    body = {
        "content": caption[:2200],
        "mediaItems": [{"type": "video", "url": video_url}],
        "platforms": [{"platform": "tiktok", "accountId": account_id()}],
        "tiktokSettings": {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "allow_comment": True,
            "allow_duet": True,
            "allow_stitch": True,
            "videoMadeWithAi": True,
            "content_preview_confirmed": True,
            "express_consent_given": True,
        },
    }
    if when:
        body["scheduledFor"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        body["publishNow"] = True
    r = requests.post(f"{API}/posts", headers=_headers(), json=body, timeout=120)
    if r.status_code == 409:
        raise AlreadyPosted("schon bei TikTok")
    out = _check(r, "post")
    states = [p.get("status") for p in (out.get("post") or {}).get("platforms", [])]
    warn = f", Hinweise: {'; '.join(out['warnings'])[:200]}" if out.get("warnings") else ""
    plan = f" fuer {when:%H:%M} UTC geplant" if when else ""
    return f"TikTok: an Zernio uebergeben{plan} (Status {', '.join(map(str, states)) or '?'}){warn}"
