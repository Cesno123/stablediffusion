# Radio-Tausch

Android-App: Du hörst einen lokalen Radiosender (z. B. Radio Köln) mit Moderation,
Nachrichten und Werbung. Sobald der Sender ein Lied spielt, schaltet die App das
Radio stumm und spielt stattdessen ein Lied aus deinen Spotify-Lieblingssongs.
Ist das Spotify-Lied zu Ende, geht es mit dem Radio weiter.

## Wie es funktioniert

1. Das Radio läuft ständig im Hintergrund mit, auch wenn es stumm ist.
2. Eine kleine KI von Google (YAMNet) hört etwa jede Sekunde hin: Musik oder Sprache?
3. Ist 4 Sekunden am Stück Musik → Radio stumm, Spotify „Play“.
4. Wechselt Spotify zum nächsten Lied → Spotify „Pause“, Radio wieder laut.
   Läuft im Radio dann noch Musik, darf Spotify einfach weiterspielen.

Die App drückt bei Spotify nur Play und Pause, wie die Tasten am Kopfhörer.
Sie braucht dafür keine Spotify-Entwicklerfreischaltung.

## Bekannte Grenzen

- Die ersten ~4 Sekunden jedes Radio-Lieds hört man noch (so lange braucht die Erkennung).
- Ist dein Spotify-Lied länger als das Radio-Lied, verpasst du die Moderation dazwischen
  (das Radio läuft live weiter).
- Werbung mit Musik oder Moderation über Musik kann falsch erkannt werden.
- Wenn Android Spotify im Hintergrund beendet, muss man Spotify neu öffnen.

## Sender wählen

Oben auf die Senderkarte tippen → suchen (über 50.000 Sender weltweit aus radio-browser.info) → antippen.
Läuft die App schon, wird sofort umgeschaltet.

## Installieren

Siehe die Releases-Seite des Repos: neueste `RadioTausch.apk` auf dem Handy herunterladen.
