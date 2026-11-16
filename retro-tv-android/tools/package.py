"""Packt build/ zu build/unsigned.apk (resources.arsc unkomprimiert und 4-Byte-ausgerichtet)."""
import os, sys, zipfile
build = sys.argv[1]
apk = os.path.join(build, "unsigned.apk")
with zipfile.ZipFile(apk, "w") as z:
    z.write(os.path.join(build, "resources.arsc"), "resources.arsc", zipfile.ZIP_STORED)
    z.write(os.path.join(build, "AndroidManifest.xml"), "AndroidManifest.xml", zipfile.ZIP_DEFLATED)
    z.write(os.path.join(build, "classes.dex"), "classes.dex", zipfile.ZIP_DEFLATED)
    for f in ("banner.png", "icon.png"):   # PNGs unkomprimiert, wie aapt es macht
        z.write(os.path.join("app/res/drawable", f), "res/drawable/" + f, zipfile.ZIP_STORED)
with zipfile.ZipFile(apk) as z:
    info = z.getinfo("resources.arsc")
    offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
    assert info.compress_type == zipfile.ZIP_STORED and offset % 4 == 0, offset
