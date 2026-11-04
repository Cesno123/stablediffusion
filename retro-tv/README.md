# Röhrenkiste – privates Retro-Fernsehen 1970–2015

Fernsehen wie früher: Jahrzehnt (70er–10er) und Kanal wählen, AN tippen, und es läuft,
was laut Sendeplan „gerade gesendet wird“. Kein Server, keine eigenen Videos – die Seite
sucht in ARD/ZDF-Mediatheken, Internet Archive, Dailymotion und (mit eigenem Schlüssel)
YouTube und spielt die Treffer nach Uhrzeit ab.

**Quellen:** YouTube (eigener Schlüssel), ARD/ZDF-Mediatheken, Internet Archive, Dailymotion,
PeerTube, Europeana/EUscreen, Wikimedia Commons.

## Auf Netlify einrichten (empfohlen)
1. app.netlify.com → **Add new project → Import an existing project → GitHub**.
2. Repo `Cesno123/stablediffusion` wählen.
3. **Branch:** `ccr-1ce6e63a-5dn7fu` · **Base directory:** `retro-tv` · Build command leer lassen.
4. **Deploy**. Danach unter *Project configuration → Change project name* z. B. `roehrenkiste`.
5. YouTube-Schlüssel in der Google Cloud Console auf `https://DEINNAME.netlify.app/*` beschränken.

Netlify stellt zusätzlich `netlify/functions/proxy.mjs` bereit: Blockiert der Browser eine
Quellen-Suche (CORS), läuft sie darüber. Der Proxy leitet nur an die Such-Schnittstellen der
obigen Quellen weiter.

Ohne Netlify geht es auch: https://raw.githack.com/Cesno123/stablediffusion/ccr-1ce6e63a-5dn7fu/retro-tv/index.html
(ohne Proxy, und Dailymotion zeigt dort „Forbidden“).

## Bedienung
- **AN/AUS** schaltet ein (Handys erlauben Ton erst nach einem Tipp).
- **CH− / CH+** Kanal, **⏮ / ⏭** eigene Auswahl blättern, **LIVE** zurück zum Sendeplan.
- **☆ MERKEN** legt die Sendung in Kanal 15 „Gemerkt“.
- **NEU SUCHEN** ignoriert den 24-Stunden-Zwischenspeicher.

## Anpassen
Oben im Skript von `index.html`: `DECADES` (Jahrzehnte) und `CHANNELS` (Suchbegriffe, mit `|` getrennt).

## Grenzen
- Jahrzehnt-Zuordnung: Internet Archive liefert ein Jahr; bei den anderen Quellen wird eine
  Jahreszahl im Titel/Text gesucht. Treffer ohne Jahreszahl können danebenliegen.
- Fehlt eine Dauer, werden 30 Minuten angenommen; endet die Sendung früher, kommt ein Pausenbild.
- Viele Uploads auf Archive/Dailymotion/YouTube stammen nicht von den Rechteinhabern.

## Fire TV / Fernseher-Browser
Seite im Browser des Fernsehers öffnen (z. B. Silk auf Fire TV). Der TV-Modus startet dort
automatisch (sonst Knopf „TV-Modus“ unten auf der Seite oder `?tv=1` an die Adresse hängen).
Fernbedienung: ▲▼ Kanal · ◀▶ Jahrzehnt · OK einschalten / Programmübersicht · ⏩⏪ Sendung · ⏯ zurück zu Live.

## YouTube-Schlüssel für alle Geräte
In Netlify unter *Project configuration → Environment variables* die Variable `YOUTUBE_API_KEY`
mit dem Schlüssel anlegen und neu deployen. Der Proxy hängt ihn an YouTube-Abfragen an;
der Schlüssel erscheint nie im Browser oder im Repo. Ein im Browser eingetragener Schlüssel hat Vorrang.
