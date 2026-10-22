"""Publish a reel through the official Instagram API (Instagram Login).

Needs a professional (business or creator) account and two environment
variables:
  IG_USER_ID       numeric Instagram user id of the account
  IG_ACCESS_TOKEN  long-lived Instagram user access token
                   (scopes: instagram_business_basic, instagram_business_content_publish)

The video is sent with a resumable upload, so it needs no public URL.
Pass --video-url instead if the file is already hosted somewhere public.

Long-lived tokens expire after 60 days; --refresh-token prints a fresh one
(the old token must still be valid and at least 24 hours old).
"""

import argparse
import os
import sys
import time

import requests

API_VERSION = os.environ.get("IG_API_VERSION", "v23.0")
GRAPH = f"https://graph.instagram.com/{API_VERSION}"
RUPLOAD = f"https://rupload.facebook.com/ig-api-upload/{API_VERSION}"


def check(resp):
    if not resp.ok:
        sys.exit(f"Instagram API error {resp.status_code}: {resp.text}")
    return resp.json()


def create_container(user_id, token, caption, video_url=None):
    data = {
        "media_type": "REELS",
        "caption": caption,
        "share_to_feed": "true",
        "thumb_offset": "4000",
        "access_token": token,
    }
    if video_url:
        data["video_url"] = video_url
    else:
        data["upload_type"] = "resumable"
    return check(requests.post(f"{GRAPH}/{user_id}/media", data=data, timeout=60))["id"]


def create_image_container(user_id, token, caption, image_url):
    """Feed photo. The API only accepts a public JPEG URL for images."""
    data = {"image_url": image_url, "caption": caption, "access_token": token}
    return check(requests.post(f"{GRAPH}/{user_id}/media", data=data, timeout=60))["id"]


def upload_file(container_id, token, path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        resp = requests.post(
            f"{RUPLOAD}/{container_id}",
            headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)},
            data=f,
            timeout=600,
        )
    check(resp)


def wait_until_ready(container_id, token, timeout=900):
    deadline = time.time() + timeout
    while time.time() < deadline:
        info = check(requests.get(
            f"{GRAPH}/{container_id}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=60,
        ))
        status = info.get("status_code")
        print(f"container {container_id}: {status}", flush=True)
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram could not process the video: {info}")
        time.sleep(15)
    sys.exit("Timed out waiting for Instagram to process the video")


def publish(user_id, token, container_id):
    return check(requests.post(
        f"{GRAPH}/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=60,
    ))["id"]


def check_access(user_id, token):
    """Read-only: confirm the token works and belongs to IG_USER_ID."""
    info = check(requests.get(
        f"{GRAPH}/me", params={"fields": "user_id,username", "access_token": token}, timeout=60))
    print(f"token belongs to @{info.get('username')}")
    if user_id and str(info.get("user_id")) != str(user_id) and str(info.get("id")) != str(user_id):
        sys.exit("IG_USER_ID does not match the account of IG_ACCESS_TOKEN")
    print("IG_USER_ID matches")


def refresh_token(token):
    info = check(requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=60,
    ))
    days = info.get("expires_in", 0) // 86400
    print(f"New token (valid ~{days} days):\n{info['access_token']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", help="local MP4 to upload")
    ap.add_argument("--video-url", help="public URL of the MP4 instead of --video")
    ap.add_argument("--image-url", help="public URL of a JPEG to post as a feed photo")
    ap.add_argument("--caption-file")
    ap.add_argument("--refresh-token", action="store_true")
    ap.add_argument("--check", action="store_true", help="verify access without posting")
    ap.add_argument("--no-publish", action="store_true",
                    help="upload and process the media but do not publish it (test)")
    args = ap.parse_args()

    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        sys.exit("IG_ACCESS_TOKEN is not set")
    if args.refresh_token:
        refresh_token(token)
        return

    user_id = os.environ.get("IG_USER_ID")
    if args.check:
        check_access(user_id, token)
        return
    if not user_id:
        sys.exit("IG_USER_ID is not set")
    if not (args.video or args.video_url or args.image_url):
        sys.exit("pass --video, --video-url or --image-url")
    caption = open(args.caption_file).read() if args.caption_file else ""

    if args.image_url:
        container = create_image_container(user_id, token, caption, args.image_url)
    elif args.video:
        # Direct (resumable) upload; fall back to the public URL if that fails.
        container = create_container(user_id, token, caption)
        try:
            upload_file(container, token, args.video)
            print("upload complete", flush=True)
        except SystemExit as e:
            if not args.video_url:
                raise
            print(f"direct upload failed ({e}), retrying via video_url", flush=True)
            container = create_container(user_id, token, caption, args.video_url)
    else:
        container = create_container(user_id, token, caption, args.video_url)
    print(f"created container {container}", flush=True)
    wait_until_ready(container, token)
    if args.no_publish:
        print("processed fine, not published (--no-publish)")
        return
    media_id = publish(user_id, token, container)
    print(f"published, media id {media_id}")


if __name__ == "__main__":
    main()
