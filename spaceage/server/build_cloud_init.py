"""Build the two setup files for a new server.

cloud-init.txt         short shell script for Hetzner's "Cloud config" field
                       (long pastes get cut or mangled on a phone)
spaceage-paket.tar.gz  the program; uploaded afterwards on http://<ip>:8080,
                       accepted only if its SHA-256 matches the script
"""

import base64
import hashlib
import io
import os
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPACEAGE = os.path.dirname(HERE)
FILES = ["ambience.py", "autogen.py", "bfl.py", "post_instagram.py", "post_queue.py", "prompt_library.py",
         "server/run.py", "server/run.sh", "server/install.sh", "server/upload.py"]

TEMPLATE = """#!/bin/bash
# SpaceAge42 setup. Replace the two HIER_EINTRAGEN below with your keys.
IG_ACCESS_TOKEN=HIER_EINTRAGEN
BFL_API_KEY=HIER_EINTRAGEN

mkdir -p /srv/spaceage/setup /opt/spaceage
exec >> /srv/spaceage/setup/log.txt 2>&1
echo "Server bereit. Jetzt die Datei spaceage-paket.tar.gz oben hochladen."
printf 'IG_ACCESS_TOKEN=%s\\nBFL_API_KEY=%s\\n' "${{IG_ACCESS_TOKEN//[[:space:]]/}}" "${{BFL_API_KEY//[[:space:]]/}}" > /etc/spaceage.env
chmod 600 /etc/spaceage.env
case "$IG_ACCESS_TOKEN$BFL_API_KEY" in *HIER_EINTRAGEN*) echo "WARNUNG: Schluessel nicht eingetragen";; esac
echo '{page}' | tr -cd 'A-Za-z0-9+/=' | base64 -d > /root/setup_upload.py
systemd-run --unit=spaceage-setup python3 /root/setup_upload.py {sha}
"""


def main():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in FILES:
            tar.add(os.path.join(SPACEAGE, name), arcname=f"spaceage/{name}")
    package = buf.getvalue()
    with open(os.path.join(HERE, "spaceage-paket.tar.gz"), "wb") as f:
        f.write(package)
    with open(os.path.join(HERE, "setup_upload.py"), "rb") as f:
        page = base64.b64encode(f.read()).decode()
    out = os.path.join(HERE, "cloud-init.txt")
    with open(out, "w") as f:
        f.write(TEMPLATE.format(page=page, sha=hashlib.sha256(package).hexdigest()))
    print(f"{out}: {os.path.getsize(out)} bytes, package {len(package)} bytes")


if __name__ == "__main__":
    main()
