# Raumschiff-Modell mit LED-Beleuchtung (eigenes Design)

Eigenes Hard-SF-Raumschiff im Stil der klassischen "Wirbelsäulen"-Schiffe: kugelförmiges Crew-Modul (Ø 72 mm) vorn,
lange Wirbelsäule mit Tankmodulen, Antenne, Reaktorblock mit vier Triebwerken. Keine Kopie eines Filmmodells.

![Vorschau](preview.png)

- Gesamtlänge: 497 mm, größtes Einzelteil 148 mm hoch (passt auf jeden Anycubic Kobra)
- Alle Teile liegen bereits in Druckausrichtung und brauchen **keine Stützstrukturen**
- `generate.py` erzeugt alle Dateien neu (`pip install manifold3d numpy`); Maße stehen oben im Skript

## Teile (Ordner `stl/`)

| Datei | Teil | Hinweis |
|---|---|---|
| 01_crew_front | Crew-Kugel vordere Hälfte, 16 Fenster | Öffnung nach unten |
| 02_crew_rear | Crew-Kugel hintere Hälfte mit Hals | Öffnung nach unten |
| 03_crew_joiner_ring | Verbindungsring | in eine Hälfte einkleben |
| 04_spine_segment_A_antenna | Wirbelsäule vorn, Loch für Antenne | stehend, Brim 5 mm |
| 05_spine_segment_B | Wirbelsäule hinten | stehend, Brim 5 mm |
| 06_antenna_dish | Antenne | Brim 5 mm, langsam drucken |
| 07_adapter_collar | Übergang Wirbelsäule → Block | breite Seite unten |
| 08_engine_block | Reaktorblock + 4 Triebwerke | Düsen nach unten |
| 09_stand_engine | Ständer hinten mit Kabelkanal | |
| 10_stand_front | Ständer vorn (Gabel unter dem Hals) | |
| 00_assembly_preview_only | Nur Vorschau | **nicht drucken** |

## Druckeinstellungen (0,2-mm-Düse)

- Schichthöhe 0,10 mm (0,08 mm für Crew-Modul und Antenne), Linienbreite 0,22 mm
- 4 Wandlinien, 15 % Füllung, PLA weiß oder hellgrau
- Geschwindigkeit Außenwand max. 40 mm/s, stehende Wirbelsäulenteile 30 mm/s
- Stützen aus, Brim wie in der Tabelle

## Beleuchtung (5 LEDs, 3 mm)

- 4 × kaltweiß oder blau: von innen durch den offenen Block in die Triebwerke stecken (Sitz Ø 3,2 mm)
- 1 × warmweiß: ins Crew-Modul, leuchtet durch die Fenster (Fenster innen mit Transparentpapier hinterkleben)
- Versorgung 5 V (USB): **jede LED bekommt einen eigenen Vorwiderstand**, alle parallel
  - weiß/blau (ca. 3,0 V, 15 mA): 150 Ω
  - warmweiß (ca. 3,0 V, 15 mA): 150 Ω, für gedimmtes Licht 330 Ω
- Kabelweg: USB-Kabel → Nut unter dem hinteren Ständer → Säule → Block. Von dort zwei dünne Litzen
  (max. 0,14 mm²) durch Übergang und Wirbelsäule (Kanal Ø 4,5 mm) ins Crew-Modul.
- Reihenfolge: erst Kabel durchfädeln und LEDs testen, dann kleben. Übergang (07) nur stecken, nicht kleben,
  damit der Block zugänglich bleibt.
