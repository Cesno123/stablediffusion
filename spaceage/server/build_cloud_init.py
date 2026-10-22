"""Write cloud-init.yaml: paste it as "Cloud config" when creating the server.

It contains the program code (packed) and three placeholders for the keys.
The server installs everything on its first start, no login needed.
"""

import base64
import io
import os
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPACEAGE = os.path.dirname(HERE)
FILES = ["ambience.py", "autogen.py", "bfl.py", "post_instagram.py", "post_queue.py", "prompt_library.py",
         "server/run.py", "server/run.sh", "server/install.sh"]

TEMPLATE = """#cloud-config
# SpaceAge42: automatic Instagram reels on your own server.
# Before creating the server, replace the two HIER_EINTRAGEN values below.
write_files:
  - path: /etc/spaceage.env
    permissions: "0600"
    content: |
      IG_ACCESS_TOKEN=HIER_EINTRAGEN
      BFL_API_KEY=HIER_EINTRAGEN
  - path: /root/spaceage.tar.gz
    encoding: b64
    content: {code}
runcmd:
  - mkdir -p /opt/spaceage
  - tar -xzf /root/spaceage.tar.gz -C /opt/spaceage
  - bash /opt/spaceage/spaceage/server/install.sh
"""


def main():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in FILES:
            tar.add(os.path.join(SPACEAGE, name), arcname=f"spaceage/{name}")
    code = base64.b64encode(buf.getvalue()).decode()
    out = os.path.join(HERE, "cloud-init.yaml")
    with open(out, "w") as f:
        f.write(TEMPLATE.format(code=code))
    print(f"{out}: {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
