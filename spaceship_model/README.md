# Raumschiff-Modell mit LED-Beleuchtung (eigenes Design)

Eigenes Hard-SF-Raumschiff im Stil der klassischen "Wirbelsäulen"-Schiffe: kugelförmiges Crew-Modul (Ø 72 mm) vorn,
lange Wirbelsäule mit Tankmodulen, Antenne, Reaktorblock mit breitem Triebwerksgehäuse und sechs Düsen (3 Spalten, je 2 übereinander). Keine Kopie eines Filmmodells.

![Vorschau](preview.png)

![Details](details.png)

- Gesamtlänge 748 mm bei 72 mm Kugeldurchmesser (Verhältnis ca. 1:10), größtes Einzelteil 260 mm hoch (für Anycubic Kobra Plus, 300 × 300 × 350 mm)
- Alle Teile liegen bereits in Druckausrichtung und brauchen **keine Stützstrukturen**
- `generate.py` erzeugt alle Dateien neu (`pip install manifold3d numpy`); Maße stehen oben im Skript

## Teile (Ordner `stl/`)

| Datei | Teil | Hinweis |
|---|---|---|
| 01_crew_front | Crew-Kugel vordere Hälfte, Cockpit mit 5 Fenstern nach vorn | Öffnung nach unten |
| 02_crew_rear | Crew-Kugel hintere Hälfte mit Hals | Öffnung nach unten |
| 03_crew_joiner_ring | Verbindungsring | in eine Hälfte einkleben |
| 04_spine_front_antenna | Wirbelsäule vorn (252 mm), Loch für den Antennenmast am hinteren Ende | stehend, **Brim 10 mm**, max. 25 mm/s |
| 05_spine_rear | Wirbelsäule hinten (252 mm) | stehend, **Brim 10 mm**, max. 25 mm/s |
| 06_antenna_dishes | Träger mit 1 großen und 2 kleinen Schüsseln | Schüsseln öffnen nach oben, langsam drucken |
| 07_antenna_mast | Mast mit Gabel | kopfüber (Gabel unten), Brim 5 mm |
| 08_adapter_collar | Übergang Wirbelsäule → Block | breite Seite unten |
| 09_engine_block | Reaktorblock + breites Gehäuse mit 6 Düsensockeln (67 mm breit) | Heckfläche nach unten |
| 10_engine_nozzle_6x | Glockendüse (Trichter, Ø 22 mm, Wand 0,8 mm) | **6× drucken**, Rand unten, langsam; Zapfen ins Heck kleben |
| 11_stand_engine | Ständer hinten mit Kabelkanal | |
| 12_stand_front | Ständer vorn (Gabel unter dem Hals) | |
| 00_assembly_preview_only | Nur Vorschau | **nicht drucken** |

## Antenne (beweglich)

- Die Schüsseln zeigen nach vorn. Der Träger kippt um ca. ±40° auf einem Scharnier, der Mast dreht sich im Loch der Wirbelsäule.
- Scharnierstift: ein 12 mm langes Stück **1,75-mm-Filament** durch Gabel und Träger schieben (sitzt in der Gabel stramm, im Träger locker).
- Mast nur einstecken, nicht kleben, wenn er drehbar bleiben soll.

## Stabilität

Die Wirbelsäule besteht aus zwei 252 mm langen Segmenten (nur eine Steckverbindung in der Mitte) und ist nur an den Enden gestützt. Steckverbindungen mit Sekundenkleber oder 2K-Kleber
verkleben und zusätzlich einen **2-mm-Stahldraht oder Carbonstab (ca. 520 mm)** durch den Kabelkanal schieben;
daneben bleibt Platz für die zwei LED-Litzen.

## Oberflächendetails

Alle Details sind aus einem Baukasten erzeugt und so ausgelegt, dass sie ohne Stützen drucken (max. ca. 1,3 mm Überstand, größere Teile mit 45°-Anlauf):

- Rohrbündel mit Schellen und Ventilen, Querleitungen zwischen Verteilern
- versenkte Kanäle (0,6 mm tief) mit innenliegender Leitung
- runde Schleusen mit Rahmen, Schrauben, Griff und Scharnier; rechteckige Türen mit Fenster
- Lüftungsgitter, genietete Wartungsplatten, Drucktanks mit Spannbändern
- Kugel: feinere Hüllenplatten, Leitungen entlang der Breiten- und Längengrade, zwei umlaufende Nuten, 5 Schleusen/Luken, Verstärkungsrippen am Hals
- Wirbelsäule: abwechselnd Tankmodule, große Drucktanks, Radiatorrippen und ein breiteres Modul mit Schleusen

## Druckeinstellungen (0,2-mm-Düse)

- Schichthöhe 0,08 mm für Crew-Kugel, Reaktorblock und Antenne, sonst 0,10 mm; Linienbreite 0,22 mm
- Die Hüllenplatten sind 0,3–0,8 mm erhaben, die Fugen 0,45 mm breit: im Slicer "dünne Wände erkennen" einschalten
- Beim vorderen Kugelteil die Naht (Z-Seam) nach hinten legen, die Fensterstege sind 1,2 mm breite Brücken
- 4 Wandlinien, 15 % Füllung, PLA weiß oder hellgrau
- Geschwindigkeit Außenwand max. 40 mm/s, stehende Wirbelsäulenteile 30 mm/s
- Stützen aus, Brim wie in der Tabelle

## Beleuchtung (7 LEDs, 3 mm)

- 6 × kaltweiß oder blau: von innen durch den offenen Block in die Sitze stecken (Ø 3,2 mm). Die LED leuchtet durch den Düsenhals in den Trichter.
  Die Kanäle der vier äußeren Düsen laufen schräg: LED mit angelöteten Litzen voran einschieben.
- 1 × warmweiß: ins Crew-Modul, leuchtet durch die Cockpitfenster (Fenster innen mit Transparentpapier hinterkleben)
- Versorgung 5 V (USB): **jede LED bekommt einen eigenen Vorwiderstand**, alle parallel
  - weiß/blau (ca. 3,0 V, 15 mA): 150 Ω
  - warmweiß (ca. 3,0 V, 15 mA): 150 Ω, für gedimmtes Licht 330 Ω
- Kabelweg: USB-Kabel → Nut unter dem hinteren Ständer → Säule → Block. Von dort zwei dünne Litzen
  (max. 0,14 mm²) durch Übergang und Wirbelsäule (Kanal Ø 4,5 mm) ins Crew-Modul.
- Reihenfolge: erst Kabel durchfädeln und LEDs testen, dann kleben. Übergang (07) nur stecken, nicht kleben,
  damit der Block zugänglich bleibt.
