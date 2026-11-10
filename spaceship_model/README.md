# Raumschiff-Modell mit LED-Beleuchtung (eigenes Design)

Eigenes Hard-SF-Raumschiff im Stil der klassischen "Wirbelsäulen"-Schiffe: kugelförmiges Crew-Modul (Ø 72 mm) vorn,
lange Wirbelsäule mit Tankmodulen, Antenne, Reaktorblock mit breitem Triebwerksgehäuse und sechs Düsen (3 Spalten, je 2 übereinander). Keine Kopie eines Filmmodells.

![Vorschau](preview.png)

![Details](details.png)

![Cockpit](cockpit.png)

![Elektronik](electronics.png)

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
| 11_stand_engine_column | Säule zwischen Batteriefach und Reaktorblock, mit Kabelkanal | stehend, Zapfen unten |
| 12_stand_front | Ständer vorn (Gabel unter dem Hals) | |
| 13_cockpit_interior | Cockpit-Einsatz: Deck, 2 Sitze, Instrumentenpult, Mittelkonsole, Rückwand mit Tür und Geräteschränken | Deck nach unten; 0,08 mm Schichthöhe |
| 14_power_base | Batteriefach (120 × 64 × 27 mm) mit Ausschnitten für Schalter und USB-C | liegt schon kopfüber: geschlossene Oberseite unten |
| 15_power_base_lid | Bodenplatte mit Halterippen für Akkuhalter, Lademodul, Spannungswandler | Rippen nach oben |
| 00_assembly_preview_only | Nur Vorschau | **nicht drucken** |

## Cockpit einbauen

1. Einsatz (13) vor dem Verkleben bemalen, z. B. Sitze dunkel, Bildschirme farbig.
2. Warmweiße LED von hinten in das Loch über der Tür stecken (Ø 3,2 mm), sie leuchtet nach vorn ins Cockpit.
3. Einsatz von der offenen Seite in die vordere Kugelhälfte (01) schieben, bis das Pult vorn unter den Fenstern anliegt
   (Rückwand sitzt 6 mm hinter der Kugelmitte), und mit wenigen Tropfen Kleber fixieren.
4. Erst danach den Verbindungsring (03) einsetzen; er wird in die **hintere** Hälfte (02) geklebt.
5. Fenster vorher von innen mit klarer Folie hinterkleben.

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

## Beleuchtung und Stromversorgung

**10 LEDs, 1 × 18650-Akku im hinteren Ständer, Schalter außen am Batteriefach, Laden über USB-C.**

### Einkaufsliste

| Anzahl | Teil | Wofür | Hinweis |
|---|---|---|---|
| 1 | 18650 Li-Ion-Zelle, 2500–3500 mAh, Markenware | Energie | flache oder Button-Top-Zelle, die in den Halter passt |
| 1 | Akkuhalter 1 × 18650 mit Litzen (ca. 76 × 21 × 19 mm) | hält die Zelle | Fach ist für bis 79 × 23 × 21,5 mm ausgelegt |
| 1 | TP4056-Lademodul **mit Schutzschaltung** (DW01), USB-C, ca. 28 × 17 mm | Laden + Tiefentlade-/Kurzschlussschutz | Anschlüsse B+/B− und OUT+/OUT− |
| 1 | MT3608 Step-up-Modul (36 × 17 mm) | macht aus 3–4,2 V stabile 5 V | **vor dem Anschließen der LEDs auf 5,0 V einstellen** |
| 1 | Mini-Wippschalter KCD11, 2-polig, Einbauausschnitt 13,5 × 9 mm | Ein/Aus | rastet von außen in die Seitenwand |
| 6 | LED 3 mm kaltweiß oder blau, klar | Triebwerke | |
| 1 | LED 3 mm warmweiß, diffus | Cockpit | |
| 3 | SMD-LED 0402, vorverdrahtet mit Kupferlackdraht, **50 cm**, **ohne** eingebauten Widerstand (3-V-Typ) | Antennenschüsseln | Sets mit Widerstand für 9–18 V sind bei 5 V zu dunkel |
| 6 | Widerstand 150 Ω, 0,25 W | Triebwerks-LEDs | je LED einer |
| 1 | Widerstand 220 Ω | Cockpit-LED | 470 Ω für gedimmtes Licht |
| 3 | Widerstand 330 Ω | Antennen-LEDs | je LED einer |
| 1 | Stück Lochrasterplatine ca. 30 × 20 mm | Verteiler im Reaktorblock | |
| 2 m | Litze 0,14 mm², rot und schwarz | Verbindungen | |
| 4 | Senkkopfschraube 3 × 10 mm (Blech- oder Kunststoffschraube) | Bodenplatte | |
| 1 | Multimeter | 5 V einstellen, Polung prüfen | unverzichtbar |
| – | Schrumpfschlauch 1,5 mm, Lötkolben, Heißkleber | | |

### Schaltung

```
18650 im Halter ──► TP4056 (B+ / B−)
                    TP4056 OUT+ ──► Schalter ──► MT3608 IN+
                    TP4056 OUT− ───────────────► MT3608 IN−
                                                 MT3608 OUT+ (5,0 V) ─┐  rot    durch die Säule
                                                 MT3608 OUT− (GND)  ──┤  schwarz  in den Reaktorblock
                                                                      ▼
                          Verteilerplatine im Reaktorblock: 5-V-Schiene und GND-Schiene
   5 V ──150 Ω──►|── GND   (6 ×, Triebwerke, LEDs in den Sitzen im Heck)
   5 V ──220 Ω──►|── GND   (1 ×, Cockpit; zwei Litzen durch die Wirbelsäule nach vorn)
   5 V ──330 Ω──►|── GND   (3 ×, Antennen; Lackdrähte durch Mast und Wirbelsäule nach hinten)
```

Alle LEDs liegen parallel, jede mit eigenem Widerstand. Geschätzter Verbrauch: ca. 100 mA bei 5 V, das sind rund 170 mA aus dem Akku
und damit grob 12–18 Stunden Leuchtdauer pro Ladung (Schätzung, nicht gemessen).

### Leitungswege im Modell

- **Batteriefach → Schiff:** zwei Litzen durch die Säule (Kanal Ø 4 mm) in den Hohlraum des Reaktorblocks.
- **Triebwerke:** sechs LEDs von innen in die Sitze stecken; die Kanäle der vier äußeren Düsen laufen schräg.
- **Cockpit:** zwei Litzen vom Block durch Übergangsstück und Wirbelsäule (Kanal Ø 4,5 mm, daneben der 2-mm-Versteifungsstab) in die Kugel, LED in das Loch über der Cockpittür.
- **Antennen:** jede Schüssel hat in der Mitte einen Sitz für eine 0402-LED mit Bohrung (Ø 0,9 mm) nach hinten. Die Lackdrähte laufen in der Nut
  auf der Rückseite des Trägers zur Mitte, mit einer **lockeren Schlaufe** (ca. 15 mm) über das Scharnier, durch den Mast (Ø 1,3 mm) und das Loch
  in der Wirbelsäule in den Hauptkanal und von dort nach hinten in den Block. Bohrungen nach dem Druck mit einem 0,8–1-mm-Bohrer freimachen.
- **Reihenfolge:** erst alle Leitungen einziehen und am Verteiler testen, dann kleben. Übergangsstück (08) nur stecken, damit der Block zugänglich bleibt.

### Sicherheit

- MT3608 **ohne angeschlossene LEDs** mit dem Multimeter auf 5,0 V drehen. Im Auslieferungszustand kann er weit mehr liefern und zerstört dann sofort alle LEDs.
- Nur ein Lademodul **mit** Schutzschaltung verwenden und die Zelle richtig herum einlegen. Li-Ion-Zellen nie kurzschließen und nicht unbeaufsichtigt laden.
- Manche dieser Lademodule laden nicht an einem USB-C-zu-USB-C-Kabel. Dann ein USB-A-zu-USB-C-Kabel nehmen.
- Die Fächer sind auf Händlerangaben ausgelegt, die je nach Hersteller um 1–3 mm abweichen. **Teile zuerst kaufen und nachmessen**, dann 14 und 15 drucken;
  die Maße stehen als `HOLDER`, `CHARGER`, `BOOST`, `SWITCH_CUT` oben im Skript.

