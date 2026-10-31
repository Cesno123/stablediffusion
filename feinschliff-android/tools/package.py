"""Zips the compiled parts into build/unsigned.apk.

resources.arsc must be stored uncompressed and 4-byte aligned (required for
apps targeting Android 11+): as the first entry its data starts at
30 + len("resources.arsc") = 44, a multiple of 4.
"""

import os
import sys
import zipfile

build = sys.argv[1]
apk = os.path.join(build, "unsigned.apk")
with zipfile.ZipFile(apk, "w") as z:
    z.write(os.path.join(build, "resources.arsc"), "resources.arsc", zipfile.ZIP_STORED)
    z.write(os.path.join(build, "AndroidManifest.xml"), "AndroidManifest.xml", zipfile.ZIP_DEFLATED)
    z.write(os.path.join(build, "classes.dex"), "classes.dex", zipfile.ZIP_DEFLATED)
    z.write(os.path.join(build, "method.xml"), "res/xml/method.xml", zipfile.ZIP_DEFLATED)
    if os.path.isdir("app/assets"):
        for root, _, files in os.walk("app/assets"):
            for f in files:
                path = os.path.join(root, f)
                z.write(path, os.path.relpath(path, "app"), zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(apk) as z:
    info = z.getinfo("resources.arsc")
    offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
    assert info.compress_type == zipfile.ZIP_STORED and offset % 4 == 0, offset
