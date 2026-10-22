# SpaceAge42 auf eigenem Server – ohne GitHub

Der Server macht dasselbe wie vorher: 4× am Tag (9:07, 13:07, 17:07, 21:07 Uhr)
ein neues FLUX-Bild aus den 60 Themen-Beschreibungen → 9:16-Reel mit Zoom und
Ton → Instagram mit deiner festen Caption. Den Instagram-Schlüssel erneuert er
alle 20 Tage selbst – keine Erinnerung mehr nötig.

Kosten: ca. 4–6 € im Monat (Server + IPv4-Adresse, Preise können sich ändern).

## Schritt 1: Neuer Instagram-Schlüssel
Der alte steckt im gesperrten GitHub-Konto fest.
developers.facebook.com → App **SpaceAgePoster** → Anwendungsfälle →
Instagram API → API-Einrichtung mit Instagram-Login → bei @_spaceage42
**Token generieren** → Text kopieren und im Handy-Notizzettel zwischenspeichern.

## Schritt 2: Neuer FLUX-Schlüssel
Auf der Black-Forest-Labs-Seite (wo du die Credits gekauft hast) → API Keys →
neuen Schlüssel erstellen und kopieren. Den alten dort löschen.

## Schritt 3: Server mieten (Hetzner)
1. hetzner.com/cloud → registrieren (Ausweis/Zahlungsmittel nötig).
2. Projekt anlegen → **Server hinzufügen**:
   - Standort: Nürnberg oder Falkenstein
   - Image: **Ubuntu 24.04**
   - Typ: der günstigste, der verfügbar ist (CX23 oder CAX11)
   - Netzwerk: **öffentliche IPv4** angehakt lassen
   - SSH-Schlüssel: überspringen
   - **Cloud config**: den kompletten Inhalt der Datei `cloud-init.txt`
     einfügen. Dann oben im Feld die zwei `HIER_EINTRAGEN` ersetzen:
     `IG_ACCESS_TOKEN=` dein Instagram-Schlüssel,
     `BFL_API_KEY=` dein FLUX-Schlüssel (ohne Leerzeichen, ohne Anführungszeichen).
3. **Erstellen & kaufen**. Notier dir die IP-Adresse (z. B. `5.75.123.45`).

## Schritt 4: Prüfen (nach ca. 5 Minuten)
Im Browser öffnen – Punkte der IP durch Bindestriche ersetzen:

    https://5-75-123-45.sslip.io/status.txt

Steht da **„Instagram-Zugang ok“** → fertig. Der erste Post kommt zur nächsten
vollen Posting-Zeit. Dieselbe Adresse zeigt immer das Ergebnis des letzten Posts.
Steht da „FEHLER …“ → Bildschirmfoto an Claude.
