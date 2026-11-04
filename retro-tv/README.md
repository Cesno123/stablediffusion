# Röhrenkiste – privates Retro-Fernsehen 1970–2015

Fernsehen wie früher: Jahrzehnt (70er–10er) und Kanal wählen, AN tippen, und es läuft,
was laut Sendeplan „gerade gesendet wird“. Kein Server, keine eigenen Videos – die Seite
sucht in ARD/ZDF-Mediatheken, Internet Archive, Dailymotion und (mit eigenem Schlüssel)
YouTube und spielt die Treffer nach Uhrzeit ab.

**Öffnen:** https://raw.githack.com/Cesno123/stablediffusion/ccr-1ce6e63a-5dn7fu/retro-tv/index.html

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
