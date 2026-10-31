"""Reads the mood of an image so the soundtrack can fit it (music.pick(..., mood=...)).

Best source: Claude looks at the picture (when ANTHROPIC_API_KEY is set in
/etc/spaceage.env) and names the mood that fits what it shows. Without a key, or if
that call fails, two free offline sources decide:
  words   the file name and caption: Midjourney downloads and our own auto images carry
          their prompt words in the name ("..._space_battle_over_jupiter_...")
  colors  brightness, saturation, warmth and how busy the picture is
Style words ("painting", "poster", "1970s") say nothing about the mood and are ignored.

The result is one of eight moods, each with the sound worlds, scales, tempos, grooves and
instruments that suit it; music.py picks freely within those, so posts still vary.
"""

import base64
import io
import json
import os
import re
import sys

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
    "action":  {"kinds": {"song": 3, "ambient": 1}, "modes": ["phrygian", "minor"], "bars": [2],
                "grooves": ["march", "motorik", "halftime"], "leads": ["brass"], "pads": ["brass"]},
    "eerie":   {"kinds": {"experimental": 1, "drone": 2, "ambient": 2}, "modes": ["phrygian", "minor"],
                "bars": [1, 2], "grooves": ["sparse", "halftime"], "leads": ["theremin", "bell"], "pads": ["strings"],
                "scales": ["phrygian", "whole tone"]},
    "neon":    {"kinds": {"song": 2, "ambient": 2}, "modes": ["minor", "dorian"], "bars": [2],
                "grooves": ["synthwave", "halftime"], "leads": ["brass", "theremin"], "pads": ["strings"]},
    "cosmic":  {"kinds": {"ambient": 3, "melodic": 1, "drone": 1}, "modes": ["lydian", "dorian"], "bars": [2],
                "grooves": ["sparse"], "leads": ["bell", "theremin"], "pads": ["strings"],
                "scales": ["lydian", "whole tone", "dorian"]},
    "gentle":  {"kinds": {"melodic": 2, "ambient": 2}, "modes": ["major", "lydian", "mixolydian"], "bars": [1, 2],
                "grooves": ["sparse", "halftime"], "leads": ["bell", "brass"], "pads": ["strings"],
                "scales": ["major", "lydian"]},
    "heroic":  {"kinds": {"song": 2, "melodic": 1, "ambient": 1}, "modes": ["mixolydian", "major", "dorian"], "bars": [2],
                "grooves": ["march", "motorik"], "leads": ["brass"], "pads": ["brass"]},
    "retro":   {"kinds": {"song": 1, "melodic": 2, "ambient": 1}, "modes": ["major", "mixolydian", "minor"], "bars": [2],
                "grooves": ["motorik", "march", "sparse"], "leads": ["theremin", "bell"], "pads": ["strings"]},
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


ASK = """You choose the soundtrack for an 8 second Instagram reel of this science fiction picture.
Look at what the picture shows (subject, action, place, light) and pick the one mood whose music fits it best:
- action: battle, chase, explosions, attack, danger in motion
- eerie: alien, horror, ruins, wrecks, fog, something unsettling or mysterious
- neon: night city, rain, cyberpunk streets, neon lights
- cosmic: open space, planets, nebulae, stars, calm vastness
- gentle: peaceful, people at ease, gardens, villages, warm and friendly scenes
- heroic: launches, expeditions, pioneers, monumental ships or stations shown with pride
- retro: playful 1950s/60s futurism, toy-like robots, flying saucers, raygun gothic
- deep: underwater, ice worlds, deep sea, frozen silence
Judge the content and the feeling, not the painting technique."""
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["mood", "reason"],
          "properties": {"mood": {"type": "string", "enum": list(WORDS)},
                         "reason": {"type": "string", "description": "a few words on what the picture shows"}}}


def ask_claude(path):
    """(mood, reason) chosen by Claude from the picture itself, or None (no key, no network, error)."""
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return None
    try:
        import anthropic

        img = Image.open(path).convert("RGB")
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        data = base64.standard_b64encode(buf.getvalue()).decode()
        client = anthropic.Anthropic(timeout=60.0)
        resp = client.messages.create(
            model=os.environ.get("SPACEAGE_MOOD_MODEL", "claude-opus-5-5"),
            max_tokens=2000,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
                {"type": "text", "text": ASK}]}],
        )
        text = next(b.text for b in resp.content if b.type == "text")
        out = json.loads(text)
        if out.get("mood") in PROFILES:
            return out["mood"], "claude: " + str(out.get("reason", ""))[:80]
    except Exception as e:  # never let the soundtrack stop a post
        print(f"mood: claude failed ({type(e).__name__}: {e}), using words and colors", file=sys.stderr, flush=True)
    return None


def mood_of(path, caption=""):
    """The mood name for an image, and a short reason (for the log)."""
    seen = ask_claude(path)
    if seen:
        return seen
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
