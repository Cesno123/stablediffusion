# Feinschliff (Android)

KI-Schreibhilfe: korrigieren, umformulieren, übersetzen, erweitern, kürzen,
Antwort vorschlagen, Text aus Fotos lesen. Auch im Textmenü jeder App
("Feinschliff"), das Ergebnis ersetzt den markierten Text.

Enthält auch die eigene Tastatur (FeinschliffIME).

Build ohne Android-SDK (`build.sh`): javac gegen das Robolectric-Framework-Jar,
dx (Maven Central), eigene Encoder für Manifest und Ressourcen (`tools/axml.py`, `tools/arsc.py`), apksig (v2).
Benötigt in `dl/`: android-all-14-robolectric-10818077.jar (als android-all.jar),
dalvik-dx-16.0.1.jar (dx.jar), apksig-2.3.0.jar; Schlüssel in `keys/release.p12`
(nicht im Repository - für Updates muss es derselbe Schlüssel sein).
