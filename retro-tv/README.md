# Röhrenkiste – privates Retro-Fernsehen

Ein „Live“-Fernsehprogramm aus alten Sendungen der öffentlich-rechtlichen Mediatheken
(ARD, ZDF, MDR, rbb …), gefunden über die Suchmaschine mediathekviewweb.de.
Kein Server und keine eigenen Videos – die Seite rechnet nur aus, was gerade „läuft“.

## Starten
- **PC:** `index.html` im Browser öffnen.
- **Handy:** Ordner z. B. auf GitHub Pages / Netlify Drop legen und die Adresse öffnen.

Bleibt die Seite beim Testbild „keine Sendungen gefunden“, blockiert der Browser die
direkte Mediathek-Suche. Dann einmal am PC `python3 build_channels.py` ausführen.
Das erzeugt `channels.js`, das die Seite automatisch nutzt.

## Kanäle ändern
Oben in `index.html` (und gleich in `build_channels.py`) steht `CHANNEL_DEFS`.
Jeder Kanal ist eine Suche, z. B. `{ name: "Krimi", query: "Stahlnetz|Der Kommissar", minMin: 40 }`.
Eigene Videos gehen auch: `items: [{title, url: "...mp4" oder "yt:VIDEO_ID", duration: Sekunden}]`.

## Grenzen
- Die Suchbegriffe sind Startpunkte und noch nicht gegen die echten Daten geprüft.
- „Jahr“ ist das Jahr der Mediathek-Veröffentlichung, nicht das Produktionsjahr.
- Depublizierte Sendungen zeigen das Testbild „Bildstörung“; dann „Sendungen neu laden“.
