"""Write cloud-init.txt: paste it as "Cloud config" when creating the server.

A plain shell script instead of YAML, because pasting on a phone easily
breaks YAML indentation. It contains the program code (packed, base64) and
two placeholders for the keys; spaces and line breaks that sneak into the
code block while copying are removed before decoding. Progress and errors
are shown on http://<ip>:8080/log.txt while the setup runs.
"""

import base64
import hashlib
import io
import os
import tarfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SPACEAGE = os.path.dirname(HERE)
FILES = ["ambience.py", "autogen.py", "bfl.py", "post_instagram.py", "post_queue.py", "prompt_library.py",
         "server/run.py", "server/run.sh", "server/install.sh"]

TEMPLATE = """#!/bin/bash
# SpaceAge42: automatic Instagram reels on your own server.
# Replace the two HIER_EINTRAGEN below with your keys, then create the server.

IG_ACCESS_TOKEN=HIER_EINTRAGEN
BFL_API_KEY=HIER_EINTRAGEN

mkdir -p /srv/spaceage/setup /opt/spaceage
exec >> /srv/spaceage/setup/log.txt 2>&1
echo "Einrichtung laeuft ... (Seite alle paar Minuten neu laden)"
systemd-run --unit=spaceage-setuplog python3 -m http.server 8080 --directory /srv/spaceage/setup

printf 'IG_ACCESS_TOKEN=%s\\nBFL_API_KEY=%s\\n' "${{IG_ACCESS_TOKEN//[[:space:]]/}}" "${{BFL_API_KEY//[[:space:]]/}}" > /etc/spaceage.env
chmod 600 /etc/spaceage.env
case "$IG_ACCESS_TOKEN$BFL_API_KEY" in *HIER_EINTRAGEN*) echo "WARNUNG: Schluessel nicht eingetragen";; esac

tr -cd 'A-Za-z0-9+/=' <<'CODE' | base64 -d > /root/spaceage.tar.gz
{code}
CODE
if [ "$(sha256sum < /root/spaceage.tar.gz | cut -c1-64)" != "{sha}" ]; then
  echo "FEHLER: Programmpaket beim Kopieren beschaedigt oder abgeschnitten"
  exit 1
fi
tar -xzf /root/spaceage.tar.gz -C /opt/spaceage
bash /opt/spaceage/spaceage/server/install.sh || echo "FEHLER beim Einrichten (siehe oben)"
"""


def main():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in FILES:
            tar.add(os.path.join(SPACEAGE, name), arcname=f"spaceage/{name}")
    data = buf.getvalue()
    code = "\n".join(textwrap.wrap(base64.b64encode(data).decode(), 76))
    out = os.path.join(HERE, "cloud-init.txt")
    with open(out, "w") as f:
        f.write(TEMPLATE.format(code=code, sha=hashlib.sha256(data).hexdigest()))
    print(f"{out}: {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
