# Röhrenkiste & Zeitkanal für Fire TV (Android-Apps)

Kleine Apps (≈12 KB), die eine Webseite bildschirmfüllend zeigen – ohne Browser, ohne Mauszeiger:

| App | Seite | APK |
|---|---|---|
| Röhrenkiste | https://zeitkan2.netlify.app (TV-Modus, startet sofort) | `Roehrenkiste.apk` |
| Zeitkanal | https://zeitkanal.netlify.app | `Zeitkanal.apk` |

Beide nutzen denselben Code (`app/src/de/spaceage/tvapp`); was sie unterscheidet, steht in `flavors/*.conf`.
Bei Seiten ohne Röhrenkiste-Schnittstelle (Zeitkanal) steuert die App das Video direkt:
⏪⏩ 30 s, ⏯ Pause; Zurück blättert zurück.
Mit `CURSOR=true` (Zeitkanal) zeigt die App einen Zeiger wie Silk: Steuerkreuz bewegt ihn
(gedrückt halten = schneller, am Rand wird geblättert), OK klickt; nach 5 s ohne Taste blendet er sich aus. Änderungen an der
Webseite kommen automatisch in der App an; die App selbst muss dafür nicht neu installiert werden.

Fernbedienung: ▲▼ Kanal · ◀▶ Jahrzehnt · OK/≡ Menü · ⏪⏩ 30 s spulen · ⏯ Pause ·
Zurück schließt das Menü, zweimal Zurück beendet die App.

## Installieren (Fire TV)
1. Fire TV: Einstellungen → Mein Fire TV → Info → 7× auf den Gerätenamen klicken (Entwickleroptionen an).
2. Appstore: App **Downloader** installieren.
3. Einstellungen → Mein Fire TV → Entwickleroptionen → Apps unbekannter Herkunft → **Downloader: an**.
4. Downloader öffnen, Adresse eingeben:
   `https://raw.githubusercontent.com/Cesno123/stablediffusion/ccr-1ce6e63a-5dn7fu/retro-tv-android/Roehrenkiste.apk`
   bzw. `…/retro-tv-android/Zeitkanal.apk`
   → Installieren → Öffnen. Die App erscheint unter „Apps“ mit eigenem Banner.

Die Webseite muss öffentlich sein (Netlify: „Make public“) oder man meldet sich einmal in der App bei Netlify an.

## Bauen (ohne Android-SDK)
`./build.sh` (alle Apps) oder `./build.sh zeitkanal` – lädt dx, apksig und das Android-Framework-Jar von Maven Central nach `dl/`,
erzeugt beim ersten Mal den Signaturschlüssel `keys/release.p12` (nicht im Repository!).
Ein Update lässt sich nur mit demselben Schlüssel über die alte App installieren; sonst die
alte App vorher deinstallieren. Neue App: `flavors/NAME.conf` anlegen (eigenes PKG!, Farben über ART_BG/ART_ACCENT) und bauen.
