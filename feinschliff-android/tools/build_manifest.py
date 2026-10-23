import sys
from axml import E, Ref, Hex, encode

PKG = "de.spaceage.feinschliff"
THEME_DAYNIGHT = Ref(0x010302E3)   # @android:style/Theme.DeviceDefault.DayNight (16974563)
ICON = Ref(0x0108003E)             # @android:drawable/ic_menu_edit (17301566)
TEXT = {"android:mimeType": "text/plain"}

def action(n): return E("action", {"android:name": n})
def category(n): return E("category", {"android:name": n})

manifest = E("manifest", {"android:versionCode": 2, "android:versionName": "1.1", "package": PKG},
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
        E("service", {"android:name": PKG + ".FeinschliffIME", "android:label": "Feinschliff",
                      "android:permission": "android.permission.BIND_INPUT_METHOD", "android:exported": True},
            E("intent-filter", {}, action("android.view.InputMethod")),
            E("meta-data", {"android:name": "android.view.im", "android:resource": Ref(0x7F010000)})),
        E("activity", {"android:name": PKG + ".ProcessTextActivity", "android:label": "Feinschliff",
                       "android:exported": True, "android:excludeFromRecents": True, "android:taskAffinity": ""},
            E("intent-filter", {}, action("android.intent.action.PROCESS_TEXT"), category("android.intent.category.DEFAULT"),
              E("data", dict(TEXT))))))

open(sys.argv[1], "wb").write(encode(manifest))

# res/xml/method.xml: describes the keyboard to the system (resource 0x7f010000 in resources.arsc)
method = E("input-method", {"android:settingsActivity": PKG + ".MainActivity",
                            "android:supportsSwitchingToNextInputMethod": True})
open(sys.argv[2], "wb").write(encode(method))

import arsc
open(sys.argv[3], "wb").write(arsc.encode(PKG, [("xml", [("method", "res/xml/method.xml")])]))
