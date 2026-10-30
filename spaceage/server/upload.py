"""Upload page for the owner's own images and videos (queue/).

Runs as the spaceage user on 127.0.0.1:8081; Caddy serves it under
https://<host>/upload behind a password (see install.sh). Uploaded files
go into the queue and are posted before any new FLUX image (images at random,
videos every 10th post); run.py removes each file from the queue once it is posted.

GET  /upload                 page: upload form + current queue
GET  /upload/file?name=X     a queued file (for the previews)
POST /upload/file?name=X     store the request body as a new queue file
                             (&caption=... optional, saved as X.txt)
POST /upload/delete?name=X   remove a queued file and its caption
"""

import datetime as dt
import html
import http.server
import os
import re
import shutil
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from post_queue import IMAGES, QUEUE, VIDEOS  # noqa: E402

MAX_BYTES = 300 * 1024 * 1024
POST_TIMES = "8:07, 12:07, 16:07, 20:07"

PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SpaceAge Uploads</title>
<body style="font-family:sans-serif;background:#111;color:#eee;padding:16px;max-width:640px;margin:auto">
<h2>SpaceAge Uploads</h2>
<p>Bilder (JPG, PNG, WEBP) oder Videos (MP4, MOV). Eigene Uploads werden <b>vor</b> neuen
FLUX-Bildern gepostet, Bilder in zuf&auml;lliger Reihenfolge, Videos bei jedem 10. Post.
Was gepostet ist, verschwindet automatisch aus dieser Liste. Postzeiten: {times}.</p>
<input type="file" id="f" multiple accept="image/*,video/*"><br><br>
<textarea id="c" rows="3" style="width:100%" placeholder="Eigene Bildunterschrift (optional, sonst eine wechselnde)"></textarea><br>
<button id="b" style="font-size:18px;padding:8px 16px">Hochladen</button>
<p id="r"></p>
<h3>Warteschlange ({count})</h3>{items}
<script>
b.onclick = async () => {{
  const files = [...f.files]; if (!files.length) return;
  for (const [i, file] of files.entries()) {{
    r.textContent = `l\\u00e4dt hoch ${{i + 1}} / ${{files.length}}: ${{file.name}} ...`;
    const q = new URLSearchParams({{name: file.name, caption: c.value}});
    const x = await fetch("/upload/file?" + q, {{method: "POST", body: file}});
    if (!x.ok) {{ r.textContent = file.name + ": " + await x.text(); return; }}
  }}
  location.reload();
}};
async function del(name) {{
  if (!confirm(name + " l\\u00f6schen?")) return;
  await fetch("/upload/delete?" + new URLSearchParams({{name}}), {{method: "POST"}});
  location.reload();
}}
</script>"""

ITEM = """<div style="display:flex;gap:12px;align-items:center;margin:8px 0">{preview}
<div style="flex:1;word-break:break-all;font-size:13px">{nr}. {name}{caption}</div>
<button onclick="del({js})">L&ouml;schen</button></div>"""


def queued():
    names = [n for n in os.listdir(QUEUE) if os.path.splitext(n)[1].lower() in IMAGES | VIDEOS]
    return sorted(names, key=lambda n: (os.path.getmtime(os.path.join(QUEUE, n)), n))


def safe_name(name):
    """Plain file name inside the queue, or None."""
    name = os.path.basename(name or "")
    return name if name and not name.startswith(".") and name in os.listdir(QUEUE) else None


class Handler(http.server.BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def params(self):
        url = urllib.parse.urlparse(self.path)
        return url.path.rstrip("/"), {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}

    def do_GET(self):
        path, q = self.params()
        if path == "/upload/file":
            name = safe_name(q.get("name"))
            if not name:
                return self.reply(404, "nicht gefunden")
            with open(os.path.join(QUEUE, name), "rb") as f:
                ctype = "video/mp4" if os.path.splitext(name)[1].lower() in VIDEOS else "image/jpeg"
                return self.reply(200, f.read(), ctype)
        items = []
        for nr, name in enumerate(queued(), 1):
            src = "/upload/file?" + urllib.parse.urlencode({"name": name})
            preview = (f'<video src="{src}" width="90" muted></video>'
                       if os.path.splitext(name)[1].lower() in VIDEOS
                       else f'<img src="{src}" width="90" loading="lazy">')
            txt = os.path.join(QUEUE, os.path.splitext(name)[0] + ".txt")
            caption = "<br><i>eigene Bildunterschrift</i>" if os.path.exists(txt) else ""
            items.append(ITEM.format(preview=preview, nr=nr, name=html.escape(name), caption=caption,
                                     js=html.escape(repr(name))))
        body = "".join(items) or "<p>leer &ndash; es werden FLUX-Bilder erzeugt</p>"
        self.reply(200, PAGE.format(times=POST_TIMES, count=len(items), items=body), "text/html; charset=utf-8")

    def do_POST(self):
        path, q = self.params()
        if path == "/upload/delete":
            name = safe_name(q.get("name"))
            if name:
                os.remove(os.path.join(QUEUE, name))
                txt = os.path.join(QUEUE, os.path.splitext(name)[0] + ".txt")
                if os.path.exists(txt):
                    os.remove(txt)
            return self.reply(200, "ok")
        if path != "/upload/file":
            return self.reply(404, "nicht gefunden")
        stem, ext = os.path.splitext(os.path.basename(q.get("name", "")))
        size = int(self.headers.get("Content-Length", 0))
        if ext.lower() not in IMAGES | VIDEOS:
            return self.reply(400, "Nur JPG, PNG, WEBP, MP4 oder MOV")
        if not 0 < size <= MAX_BYTES:
            return self.reply(400, "Datei leer oder groesser als 300 MB")
        stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-.")[:80] or "upload"
        name = f"{dt.datetime.now():%Y%m%d-%H%M%S}-{stem}{ext.lower()}"
        tmp = os.path.join(QUEUE, "." + name + ".part")  # hidden until complete
        with open(tmp, "wb") as f:
            remaining = size
            while remaining:
                chunk = self.rfile.read(min(remaining, 1 << 20))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        if remaining:
            os.remove(tmp)
            return self.reply(400, "Upload abgebrochen")
        caption = q.get("caption", "").strip()
        if caption:
            with open(os.path.join(QUEUE, os.path.splitext(name)[0] + ".txt"), "w") as f:
                f.write(caption + "\n")
        shutil.move(tmp, os.path.join(QUEUE, name))
        self.reply(200, "ok")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", 8081), Handler).serve_forever()
