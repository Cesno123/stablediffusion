# SpaceAge – automatische Sci-Fi-Reels für @_spaceage42

## GPU-Pipeline (Kaggle) – Hauptweg

GitHub Actions schickt einen Job an ein kostenloses Kaggle-GPU-Notebook:
FLUX.1-schnell malt Standbilder im Stil alter Sci-Fi-Cover (`covers.py`),
LTX-Video macht aus einigen davon echte Videoclips. Ergebnis: Release-Seite
`cover-…` mit `bild_N.png`, `reel_N.mp4` und Captions.

Einrichtung:

1. Kaggle: *Settings → Phone verification* (ohne gibt es keine GPU / kein Internet).
2. Kaggle: *Settings → API → Generate New Token*, Token kopieren
   (**niemandem schicken, nirgends posten**).
3. GitHub: *Settings → Secrets and variables → Actions → New repository secret*
   - `KAGGLE_API_TOKEN` = der Token (`KGAT_…`)
   - `KAGGLE_USERNAME` = dein Kaggle-Benutzername
4. *Actions → SpaceAge Kaggle render → Run workflow* (bzw. läuft bei Änderungen
   an `covers.py` automatisch). Dauer ca. 20–40 min.

Neue Motive: Einträge in `SCENES` in `covers.py` (Szene + Bewegung).

---

## CPU-Fallback (alt)

Der folgende Weg animiert SD-Turbo-Standbilder ohne GPU. Qualität deutlich
schlechter; nur noch manuell startbar.

Kostenlose Pipeline: GitHub Actions erzeugt jeden Tag ein 10-Sekunden-Reel
(1080×1920, mit Sound) und postet es auf Wunsch über die offizielle
Instagram-API. Keine bezahlten Anbieter.

```
Idee (ideas.py) → 3 Bilder (SD-Turbo, CPU) → Animation + Effekte + Text → Drone-Sound → MP4 → Instagram
```

Stile: cyberpunk, retro70s, anime, cosmic_horror, solarpunk, found_footage,
space_opera, synthwave. Neue Stile/Motive einfach in `ideas.py` ergänzen.

## Lokal testen

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r spaceage/requirements.txt
python spaceage/make_reel.py --out out            # mit KI (lädt ~2,5 GB Modell)
python spaceage/make_reel.py --out out --no-ai    # ohne KI, nur zum Testen
```

## Einrichtung (einmalig)

1. **GitHub Actions aktivieren**: Repo → Tab *Actions* → Workflows erlauben
   (bei Forks standardmäßig aus).
2. **Auf den Standard-Branch mergen**: Zeitgesteuerte Läufe (`schedule`)
   laufen nur vom Standard-Branch.
3. **Instagram-Zugang holen** (Konto muss *Professionell* sein):
   1. Auf <https://developers.facebook.com> eine App anlegen (Typ *Business*),
      Produkt **Instagram** → *API setup with Instagram login* hinzufügen.
   2. Dort deinen Instagram-Account verbinden und **Token generieren**
      (Berechtigungen `instagram_business_basic`,
      `instagram_business_content_publish`).
   3. Die angezeigte numerische **Instagram-User-ID** und den **Token** notieren.
4. **Secrets speichern**: Repo → *Settings → Secrets and variables → Actions*
   - Secret `IG_USER_ID`
   - Secret `IG_ACCESS_TOKEN`
5. **Freigabe einrichten (empfohlen)**: *Settings → Environments → New
   environment* `instagram` → *Required reviewers* = du selbst. Dann wartet
   jeder Post auf deinen Klick (Mail/App-Benachrichtigung von GitHub).
6. **Automatik einschalten**: *Settings → Secrets and variables → Actions →
   Variables* → `SPACEAGE_AUTOPOST` = `true`.

Ohne Schritt 6 werden täglich nur Videos erzeugt, aber nichts gepostet.

## Reels ansehen

Jedes Reel landet als MP4 unter **Releases**:
<https://github.com/Cesno123/stablediffusion/releases> – `reel.mp4` antippen,
fertig (kein Entpacken). Die Caption steht als Text darunter. Von dort kannst
du ein Reel auch von Hand in der Instagram-App posten oder einplanen.

## Manuell starten

*Actions → SpaceAge reel → Run workflow* – Optionen: posten ja/nein, ohne KI,
eigener Seed.

## Bekannte Grenzen

- **Token läuft nach 60 Tagen ab.** Vorher erneuern:
  `IG_ACCESS_TOKEN=... python spaceage/post_instagram.py --refresh-token`
  und das neue Secret speichern.
- Das sind animierte KI-Bilder, keine echten KI-Videos.
- Instagram verlangt bei realistischen KI-Inhalten die Kennzeichnung
  „KI-generiert"; die API setzt sie nicht automatisch.
- Modell-Lizenz SD-Turbo: vor Monetarisierung die aktuelle Lizenz auf
  Hugging Face prüfen.
