#!/bin/bash
# Baut und signiert Fire-TV-Apps ohne Android-SDK (javac, dx, eigene AXML/ARSC-Encoder, apksig).
# Aufruf: ./build.sh            -> alle Apps aus flavors/*.conf
#         ./build.sh zeitkanal  -> nur flavors/zeitkanal.conf
set -euo pipefail
cd "$(dirname "$0")"
M=https://repo1.maven.org/maven2
mkdir -p dl keys
get() { [ -s "dl/$2" ] || curl -sS -fL --retry 4 --retry-delay 20 -o "dl/$2" "$M/$1"; }
get com/jakewharton/android/repackaged/dalvik-dx/16.0.1/dalvik-dx-16.0.1.jar dx.jar
get com/android/tools/build/apksig/2.3.0/apksig-2.3.0.jar apksig.jar
get org/robolectric/android-all/14-robolectric-10818077/android-all-14-robolectric-10818077.jar android-all.jar
# Signaturschlüssel: Updates brauchen denselben Schlüssel – keys/ nicht löschen, nicht ins Repo
[ -s keys/release.p12 ] || keytool -genkeypair -keystore keys/release.p12 -storetype PKCS12 -storepass roehrenkiste \
  -alias roehrenkiste -keyalg RSA -keysize 2048 -validity 20000 -dname "CN=Roehrenkiste" 2>&1 | grep -v JAVA_TOOL_OPTIONS || true
mkdir -p build/signer
javac -nowarn -cp dl/apksig.jar -d build/signer tools/signer/Sign.java 2>&1 | grep -v JAVA_TOOL_OPTIONS || true

build() {
  local conf="flavors/$1.conf"
  # shellcheck disable=SC1090
  source "$conf"
  local B="build/$1"
  rm -rf "$B" && mkdir -p "$B/classes" "$B/gen/de/spaceage/tvapp"
  printf 'package de.spaceage.tvapp;\nfinal class Config { static final String URL = "%s"; static final boolean CURSOR = %s; }\n' "$URL" "${CURSOR:-false}" > "$B/gen/de/spaceage/tvapp/Config.java"
  javac -nowarn -encoding UTF-8 --release 8 -cp dl/android-all.jar -d "$B/classes" $(find app/src "$B/gen" -name '*.java') 2>&1 | grep -v "JAVA_TOOL_OPTIONS\|^Note:" || true
  java -cp dl/dx.jar com.android.dx.command.Main --dex --min-sdk-version=24 --output="$B/classes.dex" "$B/classes" 2>&1 | grep -v JAVA_TOOL_OPTIONS || true
  python3 tools/make_art.py "$B" "$ART" "$ART_BG" "$ART_ACCENT"
  (cd tools && python3 build_manifest.py "../$B/AndroidManifest.xml" "../$B/resources.arsc" "$PKG" "$LABEL" "$VERSION_CODE" "$VERSION_NAME")
  python3 tools/package.py "$B"
  java --add-exports java.base/sun.security.x509=ALL-UNNAMED --add-exports java.base/sun.security.pkcs=ALL-UNNAMED \
       --add-exports java.base/sun.security.util=ALL-UNNAMED -cp dl/apksig.jar:build/signer \
       Sign keys/release.p12 roehrenkiste "$B/unsigned.apk" "$APK" 2>&1 | grep -v JAVA_TOOL_OPTIONS
  ls -la "$APK"
}

if [ $# -gt 0 ]; then for f in "$@"; do build "$f"; done
else for c in flavors/*.conf; do build "$(basename "$c" .conf)"; done; fi
