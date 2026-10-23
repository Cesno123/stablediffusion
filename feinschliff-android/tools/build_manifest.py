import sys
from axml import E, Ref, Hex, encode

PKG = "de.spaceage.feinschliff"
THEME_DAYNIGHT = Ref(0x010302E3)   # @android:style/Theme.DeviceDefault.DayNight (16974563)
ICON = Ref(0x0108003E)             # @android:drawable/ic_menu_edit (17301566)
TEXT = {"android:mimeType": "text/plain"}

def action(n): return E("action", {"android:name": n})
def category(n): return E("category", {"android:name": n})

manifest = E("manifest", {"android:versionCode": 1, "android:versionName": "1.0", "package": PKG},
    E("uses-sdk", {"android:minSdkVersion": 26, "android:targetSdkVersion": 34}),
    E("uses-permission", {"android:name": "android.permission.INTERNET"}),
    E("application", {"android:label": "Feinschliff", "android:icon": ICON, "android:theme": THEME_DAYNIGHT,
                      "android:allowBackup": False},
        E("activity", {"android:name": PKG + ".MainActivity", "android:exported": True,
                       "android:windowSoftInputMode": Hex(0x10)},
            E("intent-filter", {}, action("android.intent.action.MAIN"), category("android.intent.category.LAUNCHER")),
            E("intent-filter", {}, action("android.intent.action.SEND"), category("android.intent.category.DEFAULT"),
              E("data", dict(TEXT))),
            E("intent-filter", {}, action("android.intent.action.SEND"), category("android.intent.category.DEFAULT"),
              E("data", {"android:mimeType": "image/*"}))),
        E("activity", {"android:name": PKG + ".ProcessTextActivity", "android:label": "Feinschliff",
                       "android:exported": True, "android:excludeFromRecents": True, "android:taskAffinity": ""},
            E("intent-filter", {}, action("android.intent.action.PROCESS_TEXT"), category("android.intent.category.DEFAULT"),
              E("data", dict(TEXT))))))

open(sys.argv[1], "wb").write(encode(manifest))
