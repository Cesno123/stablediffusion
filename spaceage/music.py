"""A tiny random composer: a short sci-fi track in the manner of a film score.

song() writes a stereo WAV that fits one or two slow bars into the clip,
so the reel loops seamlessly. Every seed gives a different piece:
  drums   a slow groove (kick, snare, hats), or none
  bass    long held roots following the chords
  chords  a progression held by a pad (string or brass ensemble)
  melody  a few long sustained notes (or none), chord tones resolving to the root,
          played by a lead sound (polyphonic brass, theremin, bell)
Busy melodies and fast patterns are avoided on purpose: in an 8 second reel they
come across as tinkling, not as music.
Sound sources come from ambience.py (analog-style oscillators and filter).

experimental() writes an unpredictable piece (odd meters, glitch stutters,
reversed swells, glissandi, metallic clicks, sudden silences), and pick()
chooses one of five sound worlds per reel - quiet drone, ambient layers,
song with beat, song without beat, experimental - never the same kind twice
in a row.
"""

import os

import numpy as np

from ambience import SR, echo, hz, lowpass_noise, resonant_lowpass, saw, soundtrack, synth_audio, write_wav

SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "dorian": [0, 2, 3, 5, 7, 9, 10],
          "phrygian": [0, 1, 3, 5, 7, 8, 10], "major": [0, 2, 4, 5, 7, 9, 11],
          "lydian": [0, 2, 4, 6, 7, 9, 11], "mixolydian": [0, 2, 4, 5, 7, 9, 10]}
# chord roots as scale degrees, one chord per bar
PROGRESSIONS = {"minor": [[0, 5, 2, 6], [0, 3, 4, 0], [0, 5, 3, 4], [0, 6, 5, 6], [0, 0, 5, 6]],
                "major": [[0, 4, 5, 3], [0, 3, 4, 4], [0, 5, 3, 4], [0, 3, 0, 4]]}
# 16 steps per bar: K kick, S snare, H closed hat, O open hat, . rest
GROOVES = {
    "motorik":   ("K...K...K...K...", "....S.......S...", "........O......."),
    "synthwave": ("K.......K.......", "....S.......S...", "..O...O...O...O."),
    "halftime":  ("K.........K.....", "........S.......", "H...H...H...H..."),
    "march":     ("K...K...K...K...", "....S.......S...", "................"),
    "sparse":    ("K.........K.....", "............S...", "................"),
}
BASS = {"root": [0, 8], "long": [0]}
# melody: steps where a note starts within one bar (16 steps); empty = rest
MELODY_RHYTHMS = [[0], [0], [0, 8], [8], [], [0, 12]]
LEADS = ["brass", "theremin", "bell"]


# ------------------------------------------------------------------ sounds

def envelope(n, attack, release):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.minimum(1, np.maximum(0, (n / SR - t) / max(release, 1e-4)))


def kick(n):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-35 * t)) / SR) * np.exp(-7 * t)


def snare(rng, n):
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    noise = noise - np.convolve(noise, np.ones(8) / 8, mode="same")  # crude high-pass
    return (0.8 * noise * np.exp(-18 * t) + 0.5 * np.sin(2 * np.pi * 185 * t) * np.exp(-25 * t))


def hat(rng, n, open_):
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    noise = noise - np.convolve(noise, np.ones(4) / 4, mode="same")
    return noise * np.exp(-(12 if open_ else 70) * t) * 0.5


def voice(kind, midi, n, rng):
    """One note of a pitched instrument, n samples long."""
    t = np.arange(n) / SR
    f = hz(midi)
    if kind == "bass":
        x = saw(f, t, 2500)
        return resonant_lowpass(x, 180 + 1400 * np.exp(-9 * t), 3.0) * envelope(n, 0.003, 0.03)
    if kind == "brass":
        vib = 1 + 0.006 * np.minimum(1, t / 0.4) * np.sin(2 * np.pi * 5.5 * t)
        x = saw(f * vib * 0.997, t, 4000) + saw(f * vib * 1.003, t, 4000)
        return resonant_lowpass(x, 500 + 2600 * (1 - np.exp(-t / 0.15)), 1.3) * envelope(n, 0.04, 0.08)
    if kind == "theremin":
        vib = 1 + 0.012 * np.sin(2 * np.pi * 6 * t)
        return np.sin(2 * np.pi * np.cumsum(f * vib) / SR) * envelope(n, 0.06, 0.08)
    if kind == "bell":  # FM bell
        mod = 3.5 * np.exp(-4 * t) * np.sin(2 * np.pi * f * 3.5 * t)
        return np.sin(2 * np.pi * f * t + mod) * np.exp(-3 * t) * envelope(n, 0.002, 0.05)
    if kind == "square":
        x = np.sign(np.sin(2 * np.pi * f * t)) * 0.6
        return resonant_lowpass(x, 2200, 1.0) * envelope(n, 0.005, 0.05)
    # pluck
    return resonant_lowpass(saw(f, t, 5000), 300 + 4000 * np.exp(-12 * t), 2.0) * np.exp(-5 * t)


def pad_chord(kind, midis, n, rng):
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        for d in (0.995, 1.0, 1.005):
            drift = 1 + 0.002 * np.sin(2 * np.pi * rng.uniform(0.3, 0.9) * t)
            x += saw(hz(m) * d * drift, t, 2500)
    cutoff = 1500 if kind == "strings" else 600 + 1500 * (1 - np.exp(-t / 0.5))
    return resonant_lowpass(x, cutoff, 0.9) * envelope(n, 0.25, 0.25)


# ------------------------------------------------------------------ composer

def place(buf, start, sound):
    s = int(start)
    if s >= len(buf):
        return
    sound = sound[:len(buf) - s]
    buf[s:s + len(sound)] += sound


def song(path, seconds, seed, drums_on=True, prefs=None):
    """Write a random piece; returns a short description. prefs (mood.py) narrows the random choices."""
    rng = np.random.default_rng(seed)
    prefs = prefs or {}
    bars = min(2, int(rng.choice(prefs.get("bars", [1, 2]))))
    bar = seconds / bars          # in an 8 s reel: 1 bar = 30 bpm feel, 2 bars = 60 bpm
    step = bar / 16
    n = int(seconds * SR)
    groove = str(rng.choice([g for g in prefs.get("grooves", list(GROOVES)) if g in GROOVES] or list(GROOVES)))
    mode = str(rng.choice(prefs.get("modes", list(SCALES))))
    family = "minor" if SCALES[mode][2] == 3 else "major"
    prog = PROGRESSIONS[family][rng.integers(len(PROGRESSIONS[family]))]
    root = int(rng.integers(45, 53))  # A2 .. E3
    scale = SCALES[mode]

    def note(degree, octave=0):
        return root + 12 * (octave + degree // len(scale)) + scale[degree % len(scale)]

    lead = str(rng.choice([x for x in prefs.get("leads", LEADS) if x in LEADS] or LEADS))
    pad_kind = str(rng.choice(prefs.get("pads", ["strings", "brass"])))
    bass_style = str(rng.choice(list(BASS)))
    drums, bass, chords, melody = (np.zeros(n) for _ in range(4))

    # drums (with a small fill on the last bar)
    k, s_, h = GROOVES[groove]
    for b in range(bars if drums_on else 0):
        for i in range(16):
            at = (b * 16 + i) * step * SR
            if k[i] == "K":
                place(drums, at, kick(int(0.4 * SR)))
            if s_[i] == "S" or (b == bars - 1 and i >= 12 and rng.random() < 0.5):
                place(drums, at, snare(rng, int(0.25 * SR)) * (1 if s_[i] == "S" else 0.6))
            if h[i] in "HO":
                place(drums, at, hat(rng, int(0.3 * SR), h[i] == "O"))

    # chords, bass and a few long melody notes, one chord per bar
    with_melody = rng.random() < 0.7
    for b in range(bars):
        deg = prog[b % len(prog)] if b < bars - 1 else prog[0]  # the last bar returns home, so the loop closes
        triad = [note(deg), note(deg + 2), note(deg + 4)]
        place(chords, b * bar * SR, pad_chord(pad_kind, [m + 12 for m in triad], int(bar * SR), rng))
        for j, i in enumerate(BASS[bass_style]):
            end = BASS[bass_style][j + 1] if j + 1 < len(BASS[bass_style]) else 16
            place(bass, (b * 16 + i) * step * SR, voice("bass", note(deg) - 12, int((end - i) * step * SR), rng))
        rhythm = MELODY_RHYTHMS[rng.integers(len(MELODY_RHYTHMS))] if with_melody else []
        if b == bars - 1 and with_melody and not rhythm:
            rhythm = [0]  # always end on a note when there is a melody
        for j, i in enumerate(rhythm):
            pitch = deg + 7 + int(rng.choice([0, 2, 4]))  # a chord tone, an octave up
            if b == bars - 1 and j == len(rhythm) - 1:
                pitch = 7  # resolve to the root
            end = rhythm[j + 1] if j + 1 < len(rhythm) else 16
            length = int((end - i) * step * SR)
            place(melody, (b * 16 + i) * step * SR, voice(lead, note(pitch, 1), length, rng))

    melody = echo(melody, step * 4, 0.25)
    left = drums * 0.7 + bass * 0.5 + chords * 0.3 + melody * 0.22
    right = drums * 0.7 + bass * 0.5 + chords * 0.34 + melody * 0.18
    parts = [left / (np.abs(left).max() + 1e-9), right / (np.abs(right).max() + 1e-9)]
    mix = np.tanh(1.6 * np.stack(parts, axis=1)) / np.tanh(1.6)  # gentle glue / saturation
    t = np.arange(n) / SR
    fade = np.minimum(1, np.minimum(t / 0.02, (seconds - t) / 0.15))  # short fades keep the loop tight
    write_wav(path, mix * fade[:, None])
    beat = f"{groove} " if drums_on else "no drums, "
    lead_desc = f"{lead} lead" if with_melody else "no melody"
    return f"{beat}{int(round(60 * 4 / bar))} bpm, {mode} on {root}, {lead_desc}, {pad_kind} pad, {bass_style} bass"


# ------------------------------------------------------------ experimental

def experimental(path, seconds, seed):
    """Odd meters, glitches and unusual sounds; returns a short description."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    used = []

    def add(x, pan):
        x = x / (np.abs(x).max() + 1e-9)
        out[:, 0] += x * (1 - pan)
        out[:, 1] += x * pan

    # metallic clicks in an odd meter (5 or 7 pulses per cycle)
    if rng.random() < 0.3:
        pulses = int(rng.choice([5, 7, 9, 11]))
        cycle = seconds / int(rng.choice([2, 4]))
        accents = rng.random(pulses) < 0.5
        accents[0] = True
        click = np.zeros(n)
        for c in range(int(seconds / cycle)):
            for i in range(pulses):
                if accents[i] or rng.random() < 0.3:
                    start = int((c * cycle + i * cycle / pulses) * SR)
                    m = int(0.12 * SR)
                    tt = np.arange(m) / SR
                    f = rng.uniform(800, 4000)
                    hit = np.sin(2 * np.pi * f * tt + 4 * np.sin(2 * np.pi * f * 1.41 * tt)) * np.exp(-40 * tt)
                    place(click, start, hit * (1 if accents[i] else 0.5))
        add(click, rng.uniform(0.2, 0.8))
        used.append(f"{pulses}-pulse clicks")
    # glitch stutter: tiny chunks of a tone repeated like a broken record
    if rng.random() < 0.2:
        src = saw(hz(int(rng.integers(55, 80))), t, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t))
        glitch = np.zeros(n)
        pos = 0
        while pos < n:
            size = int(rng.uniform(0.02, 0.15) * SR)
            chunk = src[pos:pos + size]
            for r in range(int(rng.choice([1, 1, 2, 4, 8]))):
                place(glitch, pos + r * len(chunk), chunk * (0.9 ** r))
            pos += size * int(rng.integers(1, 5))
        add(resonant_lowpass(glitch, rng.uniform(1500, 5000), 2), rng.uniform(0.2, 0.8))
        used.append("glitch stutter")
    # reversed swells: decaying bells played backwards
    if rng.random() < 0.6:
        swell = np.zeros(n)
        for start in rng.uniform(0, seconds - 2, size=int(rng.integers(1, 4))):
            m = int(rng.uniform(1, 2.5) * SR)
            tt = np.arange(m) / SR
            f = hz(int(rng.integers(55, 85)))
            bell = np.sin(2 * np.pi * f * tt + 3 * np.exp(-3 * tt) * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-2 * tt)
            place(swell, start * SR, bell[::-1])
        add(swell, rng.uniform(0.2, 0.8))
        used.append("reversed swells")
    # glissandi: sliding sines like old science fiction scores
    if rng.random() < 0.6:
        f0, f1 = rng.uniform(80, 400), rng.uniform(300, 2000)
        f = f0 * (f1 / f0) ** ((np.sin(2 * np.pi * rng.uniform(0.1, 0.4) * t) + 1) / 2)
        loudness = rng.uniform(0.4, 1.0, size=int(seconds) + 1)[t.astype(int)]  # changes every second
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * loudness, rng.uniform(0.2, 0.8))
        used.append("glissandi")
    # a low noisy bed so it never sounds empty
    add(lowpass_noise(rng, n, rng.uniform(150, 600)) * 0.5, 0.5)
    # sudden silences
    for start in rng.uniform(1, seconds - 1, size=int(rng.integers(0, 3))):
        a, b = int(start * SR), int((start + rng.uniform(0.15, 0.5)) * SR)
        out[a:b] *= 0.05
    if rng.random() < 0.5:
        out[:, 0], out[:, 1] = echo(out[:, 0], 0.37, 0.4), echo(out[:, 1], 0.29, 0.4)
    fade = np.minimum(1, np.minimum(t / 0.3, (seconds - t) / 0.5))
    write_wav(path, out * fade[:, None])
    return "experimental: " + ", ".join(used or ["noise bed"])


# --------------------------------------------------------------- dispatcher

DRONE_HZ = [41.2, 49.0, 55.0, 61.7, 65.4, 73.4]
KINDS = {  # weight, writer(path, seconds, seed, prefs)
    "drone": (1.5, lambda p, s, seed, pr: synth_audio(p, s, DRONE_HZ[seed % (3 if pr.get("low") else 6)], [], seed)
              or "quiet drone"),
    "ambient": (2.5, lambda p, s, seed, pr: "ambient: " + soundtrack(p, s, seed, pr.get("scales"), pr.get("low", False))),
    "song": (1.0, lambda p, s, seed, pr: song(p, s, seed, prefs=pr)),
    "melodic": (1.5, lambda p, s, seed, pr: song(p, s, seed, drums_on=False, prefs=pr)),
    "experimental": (0.7, lambda p, s, seed, pr: experimental(p, s, seed)),
}


def pick(path, seconds, seed, history=None, mood=None):
    """Write one soundtrack and return its description.

    With a mood from mood.py ("action", "gentle", ...): the cue score.py writes for that
    mood. Without a mood: a random kind, never the previous one.
    history: optional text file remembering the kinds used so far.
    """
    from mood import profile
    from score import RECIPES, cue

    if mood in RECIPES:  # a cue written for this mood: the music follows the picture
        desc = f"{mood} -> score: {cue(path, seconds, seed, mood)}"
        if history:
            os.makedirs(os.path.dirname(history), exist_ok=True)
            with open(history, "a") as f:
                f.write("score\n")
        return desc
    rng = np.random.default_rng(seed)
    last = ""
    if history and os.path.exists(history):
        with open(history) as f:
            lines = f.read().split()
            last = lines[-1] if lines else ""
    prefs = profile(mood) or {}
    weights_of = prefs.get("kinds") or {k: w for k, (w, _) in KINDS.items()}
    kinds = [k for k in weights_of if k != last] or list(weights_of)
    weights = np.array([float(weights_of[k]) for k in kinds])
    kind = str(rng.choice(kinds, p=weights / weights.sum()))
    desc = KINDS[kind][1](path, seconds, seed, prefs)
    if mood:
        desc = f"{mood} -> {kind}: {desc}"
    if history:
        os.makedirs(os.path.dirname(history), exist_ok=True)
        with open(history, "a") as f:
            f.write(kind + "\n")
    return desc
