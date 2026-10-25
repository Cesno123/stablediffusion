"""Reads the mood of an image so the soundtrack can fit it (music.pick(..., mood=...)).

Two sources, both free and offline:
  words   the file name and caption: Midjourney downloads and our own auto images carry
          their prompt words in the name ("..._space_battle_over_jupiter_...")
  colors  brightness, saturation, warmth and how busy the picture is
Style words ("painting", "poster", "1970s") say nothing about the mood and are ignored.

The result is one of eight moods, each with the sound worlds, scales, tempos, grooves and
instruments that suit it; music.py picks freely within those, so posts still vary.
"""

import re

import numpy as np
from PIL import Image, ImageFilter

# mood -> trigger words (English prompt words and German caption words)
WORDS = {
    "action": "battle war attack attacking fight fighting fighter fighters explosion explosions laser lasers blaster invaders "
              "invasion siege chase chasing firing fleet fleets warrior mercenary dogfight combat racing race storm "
              "schlacht angriff kampf krieg explosion verfolgung",
    "eerie": "alien aliens creature monster derelict wreck ruins ruin skull biomechanical horror dark haunted fossil "
             "tentacle swamp abandoned dead eerie mysterious strange interrogation cyborg mist fog black-hole void "
             "unheimlich wrack ruine verlassen",
    "neon": "neon city megacity cyberpunk rain noir detective street streets night nightclub hacker arcade billboard "
            "skyscraper skyscrapers metropolis downtown taxi motorcycle "
            "stadt nacht regen",
    "cosmic": "nebula galaxy galaxies stars starfield cosmos cosmic orbit orbiting planet planets ring rings saturn jupiter "
              "moon moons comet asteroid eclipse sun suns dyson void drifting drift infinite universe telescope "
              "weltall sterne planet mond galaxie",
    "gentle": "garden gardens children child kite kites picnic flowers flower meadow farm farmer sheep shepherd village "
              "cottage cafe tea family families cat dog lullaby peaceful quiet sunset greenhouse orchard "
              "garten kinder blumen familie ruhe",
    "heroic": "launch launching rocket rockets cosmonaut astronaut astronauts expedition explorer explorers hero heroic "
              "landing parade spaceport shuttle mission victory construction assembling crew pioneers flag "
              "rakete start held mission",
    "retro": "retro vintage 1950s 1960s 50s 60s toy tin robot robots raygun flying-car diner jukebox "
             "theremin saucer saucers b-movie atomic googie "
             "roboter",
    "deep": "ocean underwater sea submarine whale whales diver divers ice frozen glacier europa enceladus lake reef "
            "deep abyss jellyfish coral polar arctic snow "
            "meer ozean eis tiefsee",
}
# what each mood sounds like (music.py reads these keys)
PROFILES = {
    "action":  {"kinds": {"song": 3, "experimental": 1}, "modes": ["phrygian", "minor"], "bars": [4],
                "grooves": ["breakbeat", "electro", "motorik"], "leads": ["square", "brass"], "pads": ["brass"]},
    "eerie":   {"kinds": {"experimental": 2, "drone": 2, "ambient": 1}, "modes": ["phrygian", "minor"],
                "bars": [2], "grooves": ["sparse", "halftime"], "leads": ["theremin", "bell"], "pads": ["strings"],
                "scales": ["phrygian", "whole tone"]},
    "neon":    {"kinds": {"song": 3, "melodic": 1}, "modes": ["minor", "dorian"], "bars": [3, 4],
                "grooves": ["synthwave", "halftime", "electro"], "leads": ["square", "pluck", "brass"], "pads": ["strings"]},
    "cosmic":  {"kinds": {"ambient": 3, "melodic": 1, "drone": 1}, "modes": ["lydian", "dorian"], "bars": [2],
                "grooves": ["sparse"], "leads": ["bell", "theremin"], "pads": ["strings"],
                "scales": ["lydian", "whole tone", "dorian"]},
    "gentle":  {"kinds": {"melodic": 3, "ambient": 1}, "modes": ["major", "lydian", "mixolydian"], "bars": [2, 3],
                "grooves": ["sparse", "halftime"], "leads": ["bell", "pluck"], "pads": ["strings"],
                "scales": ["major", "lydian"]},
    "heroic":  {"kinds": {"song": 3, "melodic": 1}, "modes": ["mixolydian", "major", "dorian"], "bars": [3, 4],
                "grooves": ["march", "motorik"], "leads": ["brass"], "pads": ["brass"]},
    "retro":   {"kinds": {"song": 2, "melodic": 2}, "modes": ["major", "mixolydian", "minor"], "bars": [3, 4],
                "grooves": ["motorik", "march", "sparse"], "leads": ["theremin", "square", "bell"], "pads": ["strings"]},
    "deep":    {"kinds": {"ambient": 2, "drone": 2, "melodic": 1}, "modes": ["dorian", "minor", "lydian"], "bars": [2],
                "grooves": ["sparse"], "leads": ["bell", "theremin"], "pads": ["strings"],
                "scales": ["dorian", "minor", "lydian"], "low": True},
}
_INDEX = {w: m for m, ws in WORDS.items() for w in ws.split()}


def words_of(text):
    text = re.sub(r"[_\-.]+", " ", (text or "").lower())
    return re.findall(r"[a-zäöüß0-9]+", text)


def colors(path):
    """brightness, saturation, warmth (-1 cold .. 1 warm) and busyness, each about 0..1."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((256, 256))
    a = np.asarray(img, dtype=np.float32) / 255
    r, b = a[..., 0], a[..., 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    bright = float(a.mean())
    sat = float(np.mean((mx - mn) / (mx + 1e-6)))
    warm = float(np.clip((r.mean() - b.mean()) * 4, -1, 1))
    edges = np.asarray(img.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32) / 255
    busy = float(np.clip(edges.mean() * 6, 0, 1))
    return bright, sat, warm, busy


def mood_of(path, caption=""):
    """The mood name for an image, and a short reason (for the log)."""
    score = {m: 0.0 for m in PROFILES}
    hits = []
    for w in words_of(path.rsplit("/", 1)[-1]) + words_of(caption):
        m = _INDEX.get(w)
        if m:
            score[m] += 2
            hits.append(w)
    try:
        bright, sat, warm, busy = colors(path)
    except Exception:
        bright, sat, warm, busy = 0.4, 0.4, 0.0, 0.4
    # colors break ties and decide when no words match
    score["eerie"] += (0.35 - bright) * 3 + (0.3 - sat) * 2
    score["cosmic"] += (0.3 - bright) * 2 + max(0.0, -warm)
    score["deep"] += max(0.0, -warm) * 1.5
    score["gentle"] += (bright - 0.5) * 3 + max(0.0, warm) - busy
    score["action"] += busy * 1.6 + max(0.0, warm) * 0.4 - 0.7
    score["neon"] += sat * 1.5 - bright - 0.2
    score["heroic"] += max(0.0, warm) * 0.8 + (bright - 0.4)
    score["retro"] += (sat - 0.4) + max(0.0, warm) * 0.5
    mood = max(score, key=score.get)
    why = f"words: {', '.join(hits[:5])}" if hits else "colors only"
    return mood, f"{why}; light {bright:.2f}, color {sat:.2f}, warm {warm:+.2f}, busy {busy:.2f}"


def profile(mood):
    return PROFILES.get(mood)
