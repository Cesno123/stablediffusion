"""Tiny setup page on port 8080 (only while the server is being set up).

GET /          upload form plus the live setup log
GET /log.txt   the setup log
POST /upload   the program package; it is installed only if its SHA-256
               matches the hash baked into the setup script, so nobody
               else can push code onto the server through this page.
"""

import hashlib
import http.server
import os
import subprocess
import sys

EXPECTED = sys.argv[1]
LOG = "/srv/spaceage/setup/log.txt"
PACKAGE = "/root/spaceage.tar.gz"

PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SpaceAge Einrichtung</title>
<body style="font-family:sans-serif;background:#111;color:#eee;padding:16px">
<h2>SpaceAge Einrichtung</h2>
<p>1. Datei <b>spaceage-paket.tar.gz</b> ausw&auml;hlen<br>2. Hochladen tippen</p>
<input type="file" id="f"> <button id="b">Hochladen</button>
<p id="r"></p><pre id="log" style="white-space:pre-wrap;font-size:12px"></pre>
<script>
b.onclick = () => { if (!f.files[0]) return; r.textContent = "l\\u00e4dt hoch ...";
  fetch("/upload", {method: "POST", body: f.files[0]}).then(x => x.text()).then(t => r.textContent = t); };
const poll = () => fetch("/log.txt").then(x => x.text()).then(t => log.textContent = t).catch(() => {});
poll(); setInterval(poll, 5000);
</script>"""


def log(msg):
    with open(LOG, "a") as f:
        f.write(msg + "\n")


class Handler(http.server.BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/log.txt"):
            with open(LOG) as f:
                self.reply(200, f.read())
        else:
            self.reply(200, PAGE, "text/html; charset=utf-8")

    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        if self.path != "/upload" or not 0 < size < 5_000_000:
            return self.reply(400, "Ungueltige Datei")
        data = self.rfile.read(size)
        if hashlib.sha256(data).hexdigest() != EXPECTED:
            return self.reply(400, "Falsche oder beschaedigte Datei - bitte spaceage-paket.tar.gz nehmen")
        with open(PACKAGE, "wb") as f:
            f.write(data)
        log("Paket empfangen, Installation startet ...")
        subprocess.run(["tar", "-xzf", PACKAGE, "-C", "/opt/spaceage"], check=True)
        # own unit, so install.sh can stop this page without stopping itself
        subprocess.run(["systemd-run", "--unit=spaceage-install", "-p", f"StandardOutput=append:{LOG}",
                        "-p", f"StandardError=append:{LOG}", "bash", "/opt/spaceage/spaceage/server/install.sh"],
                       check=True)
        self.reply(200, "Hochgeladen! Installation laeuft - der Fortschritt erscheint unten.")

    def log_message(self, *args):
        pass


http.server.ThreadingHTTPServer(("", 8080), Handler).serve_forever()
