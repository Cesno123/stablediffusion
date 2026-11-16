# Röhrenkiste für Fire TV (Android-App)

Kleine App (≈12 KB), die https://zeitkan2.netlify.app im TV-Modus bildschirmfüllend zeigt –
ohne Browser, ohne Mauszeiger. Startet sofort das laufende Programm. Änderungen an der
Webseite kommen automatisch in der App an; die App selbst muss dafür nicht neu installiert werden.

Fernbedienung: ▲▼ Kanal · ◀▶ Jahrzehnt · OK/≡ Menü · ⏪⏩ 30 s spulen · ⏯ Pause ·
Zurück schließt das Menü, zweimal Zurück beendet die App.

## Installieren (Fire TV)
1. Fire TV: Einstellungen → Mein Fire TV → Info → 7× auf den Gerätenamen klicken (Entwickleroptionen an).
2. Appstore: App **Downloader** installieren.
3. Einstellungen → Mein Fire TV → Entwickleroptionen → Apps unbekannter Herkunft → **Downloader: an**.
4. Downloader öffnen, Adresse eingeben:
   `https://raw.githubusercontent.com/Cesno123/stablediffusion/ccr-1ce6e63a-5dn7fu/retro-tv-android/Roehrenkiste.apk`
   → Installieren → Öffnen. Die App erscheint unter „Apps“ mit eigenem Banner.

Die Webseite muss öffentlich sein (Netlify: „Make public“) oder man meldet sich einmal in der App bei Netlify an.

## Bauen (ohne Android-SDK)
`./build.sh` – lädt dx, apksig und das Android-Framework-Jar von Maven Central nach `dl/`,
erzeugt beim ersten Mal den Signaturschlüssel `keys/release.p12` (nicht im Repository!).
Ein Update lässt sich nur mit demselben Schlüssel über die alte App installieren; sonst die
alte App vorher deinstallieren. Grafiken: `python3 tools/make_art.py app/res/drawable`.
