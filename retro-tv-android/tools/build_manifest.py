"""Schreibt AndroidManifest.xml (binär) und resources.arsc für die Röhrenkiste-TV-App."""
import sys
from axml import E, Ref, Hex, encode
import arsc

PKG = "de.spaceage.roehrenkiste"
THEME = Ref(0x0103000A)    # @android:style/Theme.Black.NoTitleBar.Fullscreen
BANNER = Ref(0x7F010000)   # res/drawable/banner.png (Kachel im Fire-TV-Startbildschirm)
ICON = Ref(0x7F010001)     # res/drawable/icon.png

def action(n): return E("action", {"android:name": n})
def category(n): return E("category", {"android:name": n})

manifest = E("manifest", {"android:versionCode": 1, "android:versionName": "1.0", "package": PKG},
    E("uses-sdk", {"android:minSdkVersion": 24, "android:targetSdkVersion": 34}),
    E("uses-permission", {"android:name": "android.permission.INTERNET"}),
    E("uses-feature", {"android:name": "android.software.leanback", "android:required": False}),
    E("uses-feature", {"android:name": "android.hardware.touchscreen", "android:required": False}),
    E("application", {"android:label": "Röhrenkiste", "android:icon": ICON, "android:banner": BANNER,
                      "android:theme": THEME, "android:hardwareAccelerated": True,
                      "android:usesCleartextTraffic": False, "android:allowBackup": False},
        E("activity", {"android:name": PKG + ".MainActivity", "android:exported": True,
                       "android:launchMode": 2,                 # singleTask
                       "android:screenOrientation": 0,          # landscape
                       "android:configChanges": Hex(0x1FF0)},   # kein Neustart bei Bildschirm-/Tastaturwechsel
            E("intent-filter", {}, action("android.intent.action.MAIN"),
              category("android.intent.category.LAUNCHER"),
              category("android.intent.category.LEANBACK_LAUNCHER")))))

open(sys.argv[1], "wb").write(encode(manifest))
open(sys.argv[2], "wb").write(arsc.encode(PKG, [("drawable", [("banner", "res/drawable/banner.png"),
                                                              ("icon", "res/drawable/icon.png")])]))
