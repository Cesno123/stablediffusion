#!/bin/bash
# Builds and signs Feinschliff.apk without the Android SDK (javac, dx, own AXML encoder, apksig).
set -euo pipefail
cd "$(dirname "$0")"
rm -rf build && mkdir -p build/classes
javac -nowarn -encoding UTF-8 --release 8 -cp dl/android-all.jar -d build/classes $(find app/src -name '*.java') 2>&1 | grep -v "JAVA_TOOL_OPTIONS\|^Note:" || true
java -cp dl/dx.jar com.android.dx.command.Main --dex --min-sdk-version=26 --output=build/classes.dex build/classes 2>&1 | grep -v JAVA_TOOL_OPTIONS || true
python3 tools/build_manifest.py build/AndroidManifest.xml
python3 - <<'PY'
import zipfile
with zipfile.ZipFile("build/unsigned.apk", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("build/AndroidManifest.xml", "AndroidManifest.xml")
    z.write("build/classes.dex", "classes.dex")
PY
java --add-exports java.base/sun.security.x509=ALL-UNNAMED --add-exports java.base/sun.security.pkcs=ALL-UNNAMED --add-exports java.base/sun.security.util=ALL-UNNAMED -cp dl/apksig.jar:tools/signer Sign keys/release.p12 feinschliff build/unsigned.apk build/Feinschliff.apk 2>&1 | grep -v JAVA_TOOL_OPTIONS
ls -la build/Feinschliff.apk
