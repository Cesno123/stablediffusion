"""One short film-score cue per picture mood (mood.py), so the music fits the motif.

Each mood has its own recipe with a clear character, varied by the seed (key,
scale, chords, instruments, small details), but never busy melodies:
  action   driving low ostinato, war drums, brass stabs (90 bpm feel)
  heroic   brass chords swelling, timpani hits and a roll into the loop, one long horn line
  eerie    low drone, dissonant string cluster, slow theremin glide, metallic clangs
  cosmic   wide lydian strings, a few high bells far away, space wind
  gentle   warm soft pad, a few music-box notes, low held bass
  neon     synthwave: pulsing filtered bass, kick and snare, dark string pad
  retro    theremin line over vibraphone chords and a walking upright bass
  deep     very deep drone, sonar pings with long echoes, rumbling water
Everything fits whole bars into the clip, so the reel loops seamlessly.
"""

import numpy as np

from ambience import SR, echo, hz, lowpass_noise, resonant_lowpass, saw, write_wav
from music import kick, place, snare, voice

SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10],
          "dorian": [0, 2, 3, 5, 7, 9, 10], "major": [0, 2, 4, 5, 7, 9, 11],
          "lydian": [0, 2, 4, 6, 7, 9, 11], "mixolydian": [0, 2, 4, 5, 7, 9, 10]}


class Cue:
    """Helper holding key, scale and time grid for one cue."""

    def __init__(self, seconds, seed, scales, bars, low, high):
        self.rng = np.random.default_rng(seed)
        self.seconds = seconds
        self.n = int(seconds * SR)
        self.t = np.arange(self.n) / SR
        self.mode = str(self.rng.choice(scales))
        self.scale = SCALES[self.mode]
        self.root = int(self.rng.integers(low, high))
        self.bars = bars
        self.bar = seconds / bars
        self.step = self.bar / 16
        self.layers = []  # (signal, gain, pan)

    def note(self, degree, octave=0):
        s = self.scale
        return self.root + 12 * (octave + degree // len(s)) + s[degree % len(s)]

    def chord(self, degree, octave=1, size=3):
        return [self.note(degree + 2 * i, octave) for i in range(size)]

    def at(self, bar, step=0):
        return (bar * 16 + step) * self.step * SR

    def add(self, sig, gain, pan=0.5):
        self.layers.append((sig, gain, pan))

    def write(self, path, fade_in=0.02, fade_out=0.2):
        left, right = np.zeros(self.n), np.zeros(self.n)
        for sig, gain, pan in self.layers:
            sig = sig[:self.n] / (np.abs(sig).max() + 1e-9) * gain
            left += sig * (1 - pan)
            right += sig * pan
        mix = np.stack([left, right], axis=1)
        mix = np.tanh(1.4 * mix / (np.abs(mix).max() + 1e-9)) / np.tanh(1.4)
        t = self.t
        fade = np.minimum(1, np.minimum(t / fade_in, (self.seconds - t) / fade_out))
        write_wav(path, mix * fade[:, None])


def ensemble(midis, n, kind, attack=0.3, release=0.4, rng=None):
    """Held chord: 'strings' (soft, wide), 'brass' (filter opens) or 'organ' (pure)."""
    rng = rng or np.random.default_rng()
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        for d in (0.996, 1.0, 1.004):
            drift = 1 + 0.003 * np.sin(2 * np.pi * rng.uniform(0.2, 0.7) * t + rng.uniform(0, 6))
            if kind == "organ":
                x += np.sin(2 * np.pi * hz(m) * d * t) + 0.3 * np.sin(4 * np.pi * hz(m) * d * t)
            else:
                x += saw(hz(m) * d * drift, t, 3000)
    if kind == "brass":
        x = resonant_lowpass(x, 350 + 2200 * (1 - np.exp(-t / 0.35)), 1.2)
    elif kind == "strings":
        x = resonant_lowpass(x, 1600, 0.8)
    env = np.minimum(1, t / attack) * np.minimum(1, np.maximum(0, (n / SR - t) / release))
    return x * env


def timpani(n, midi, strength=1.0):
    t = np.arange(n) / SR
    f = hz(midi) * (1 + 0.15 * np.exp(-20 * t))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return strength * body * np.exp(-3.5 * t)


def tom(n, midi):
    t = np.arange(n) / SR
    f = hz(midi) * (1 + 0.6 * np.exp(-25 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-9 * t)


def bell(n, midi, decay=2.5):
    t = np.arange(n) / SR
    f = hz(midi)
    mod = 2.0 * np.exp(-3 * t) * np.sin(2 * np.pi * f * 3.5 * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-decay * t) * np.minimum(1, t / 0.003)


def vibes(n, midi):
    t = np.arange(n) / SR
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 5.5 * t)
    return (np.sin(2 * np.pi * hz(midi) * t) + 0.25 * np.sin(2 * np.pi * hz(midi) * 4 * t)) * np.exp(-1.6 * t) * trem


def glide(t, midis, vib=0.012):
    """Theremin-like voice sliding between a few long notes."""
    pos = np.minimum((t / t[-1] * len(midis)).astype(int), len(midis) - 1)
    f = np.convolve(hz(np.array(midis))[pos], np.ones(SR // 3) / (SR // 3), mode="same")
    f *= 1 + vib * np.sin(2 * np.pi * 6 * t)
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) + 0.15 * np.sin(2 * phase)


# ------------------------------------------------------------------ recipes

def action(c):
    rng = c.rng
    prog = [0, 0, 5] if rng.random() < 0.5 else [0, 5, 6]
    ost = np.zeros(c.n)
    drums = np.zeros(c.n)
    stabs = np.zeros(c.n)
    pattern = "K..K..K.K..K.K.." if rng.random() < 0.5 else "K.K...K.K.K...K."
    for b in range(c.bars):
        deg = prog[b % len(prog)]
        for i in range(0, 16, 2):  # straight eighths on the root, a tension note at the end of the bar
            m = c.note(deg) - 12 if i < 14 else c.note(deg + 1) - 12
            place(ost, c.at(b, i), voice("bass", m, int(c.step * 2 * SR * 0.9), rng) * (1.0 if i % 4 == 0 else 0.7))
        for i, ch in enumerate(pattern):
            if ch == "K":
                place(drums, c.at(b, i), tom(int(0.5 * SR), 38 if i % 4 == 0 else 45))
            if i in (4, 12):
                place(drums, c.at(b, i), snare(rng, int(0.25 * SR)) * 0.35)
        place(stabs, c.at(b), ensemble(c.chord(deg, 1), int(c.step * 5 * SR), "brass", 0.02, 0.15, rng))
    c.add(ost, 0.55, 0.45)
    c.add(drums, 0.8, 0.5)
    c.add(echo(stabs, c.step * 3, 0.25), 0.45, 0.6)
    c.add(np.sin(2 * np.pi * hz(c.root - 24) * c.t), 0.25, 0.5)


def heroic(c):
    rng = c.rng
    second = int(rng.choice([3, 4, 6]))  # IV, V or bVII
    pads = np.zeros(c.n)
    timp = np.zeros(c.n)
    for b, deg in enumerate([0, second]):
        place(pads, c.at(b), ensemble(c.chord(deg, 0, 4), int(c.bar * SR), "brass", 0.6, 0.3, rng))
        place(timp, c.at(b), timpani(int(1.5 * SR), c.note(deg) - 12, 1.0))
        place(timp, c.at(b, 8), timpani(int(1.2 * SR), c.note(deg) - 12, 0.6))
    for k in range(10):  # roll leading back into bar one
        place(timp, c.at(1, 12) + k * c.step * SR * 0.4, timpani(int(0.4 * SR), c.root - 12, 0.25 + 0.06 * k))
    horn = np.zeros(c.n)
    line = [c.note(4, 1), c.note(7, 1)] if rng.random() < 0.5 else [c.note(2, 1), c.note(4, 1)]
    place(horn, c.at(0, 4), voice("brass", line[0], int(c.step * 12 * SR), rng))
    place(horn, c.at(1, 0), voice("brass", line[1], int(c.step * 14 * SR), rng))
    c.add(pads, 0.55, 0.5)
    c.add(timp, 0.6, 0.45)
    c.add(echo(horn, c.step * 4, 0.2), 0.35, 0.6)
    c.add(ensemble([c.root, c.root + 12], c.n, "strings", 1.0, 1.0, rng), 0.25, 0.4)


def eerie(c):
    rng = c.rng
    t = c.t
    c.add(np.sin(2 * np.pi * hz(c.root - 12) * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * t))
          + 0.4 * np.sin(2 * np.pi * hz(c.root - 6) * t), 0.4, 0.5)  # root and tritone
    c.add(ensemble([c.root + 12, c.root + 13, c.root + 17], c.n, "strings", 2.5, 2.0, rng), 0.35, 0.35)
    pitches = [c.root + 24 + int(x) for x in rng.choice([0, 1, 6, 7, -1], size=2, replace=False)]
    c.add(glide(t, pitches, 0.02) * np.minimum(1, t / 1.5), 0.22, 0.7)
    clangs = np.zeros(c.n)
    for start in rng.uniform(1, c.seconds - 2, size=int(rng.integers(1, 3))):
        m = int(2 * SR)
        tt = np.arange(m) / SR
        clang = np.sin(2 * np.pi * rng.uniform(200, 600) * tt) * np.sin(2 * np.pi * rng.uniform(700, 1500) * tt)
        place(clangs, start * SR, clang * np.exp(-2 * tt))
    c.add(echo(clangs, 0.45, 0.45), 0.2, float(rng.uniform(0.2, 0.8)))
    c.add(lowpass_noise(rng, c.n, 300) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)), 0.2, 0.5)


def cosmic(c):
    rng = c.rng
    t = c.t
    pads = np.zeros(c.n)
    for b, deg in enumerate([0, 1]):  # I and II: the floating lydian sound
        place(pads, c.at(b), ensemble(c.chord(deg, 1, 4), int(c.bar * SR) + int(0.5 * SR), "strings", 1.2, 1.2, rng))
    c.add(pads, 0.5, 0.5)
    c.add(np.sin(2 * np.pi * hz(c.root - 12) * t), 0.25, 0.5)
    bells = np.zeros(c.n)
    for start in np.sort(rng.uniform(0.5, c.seconds - 1.5, size=int(rng.integers(2, 4)))):
        place(bells, start * SR, bell(int(3 * SR), c.note(int(rng.choice([0, 2, 4, 6])), 3), 1.2))
    c.add(echo(bells, 0.6, 0.5, repeats=5), 0.18, float(rng.uniform(0.3, 0.7)))
    c.add(lowpass_noise(rng, c.n, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + 1)), 0.15, 0.5)


def gentle(c):
    rng = c.rng
    second = int(rng.choice([3, 5]))
    pads = np.zeros(c.n)
    bass = np.zeros(c.n)
    for b, deg in enumerate([0, second]):
        place(pads, c.at(b), ensemble(c.chord(deg, 1), int(c.bar * SR) + int(0.3 * SR), "organ", 0.8, 0.8, rng))
        place(bass, c.at(b), voice("bass", c.note(deg) - 12, int(c.bar * SR), rng))
    box = np.zeros(c.n)
    steps = sorted(rng.choice([0, 4, 8, 12, 16, 20, 24, 28], size=4, replace=False))
    for k, s in enumerate(steps):
        deg = 7 if k == len(steps) - 1 else int(rng.choice([0, 2, 4, 7]))
        place(box, c.at(0, int(s)), bell(int(2.5 * SR), c.note(deg, 2), 2.0))
    c.add(resonant_lowpass(pads, 1200, 0.7), 0.4, 0.5)
    c.add(resonant_lowpass(bass, 400, 0.7), 0.3, 0.5)
    c.add(echo(box, c.step * 6, 0.3), 0.25, 0.6)


def neon(c):
    rng = c.rng
    prog = [0, 5, 3] if rng.random() < 0.5 else [0, 6, 5]
    bass = np.zeros(c.n)
    drums = np.zeros(c.n)
    pads = np.zeros(c.n)
    for b in range(c.bars):
        deg = prog[b % len(prog)]
        for i in range(0, 16, 2):
            octave = 12 if i % 4 == 2 else 0
            place(bass, c.at(b, i), voice("bass", c.note(deg) - 12 + octave, int(c.step * 1.8 * SR), rng))
        for i in (0, 8):
            place(drums, c.at(b, i), kick(int(0.4 * SR)))
        for i in (4, 12):
            place(drums, c.at(b, i), snare(rng, int(0.3 * SR)) * 0.7)
        place(pads, c.at(b), ensemble(c.chord(deg, 1), int(c.bar * SR), "strings", 0.4, 0.3, rng))
    c.add(bass, 0.5, 0.5)
    c.add(drums + 0.3 * echo(drums, c.step * 3, 0.3), 0.6, 0.5)
    c.add(pads, 0.4, 0.55)


def retro(c):
    rng = c.rng
    vib = np.zeros(c.n)
    bass = np.zeros(c.n)
    for b, deg in enumerate([0, int(rng.choice([3, 4]))]):
        for i in (0, 8):
            for m in c.chord(deg, 1):
                place(vib, c.at(b, i), vibes(int(1.6 * SR), m))
        for k, i in enumerate((0, 4, 8, 12)):  # walking bass: root, third, fifth, sixth
            place(bass, c.at(b, i), voice("bass", c.note(deg + [0, 2, 4, 5][k]) - 12, int(c.step * 3.6 * SR), rng))
    line = [c.note(int(d), 2) for d in rng.choice([0, 2, 4, 5, 7], size=3, replace=False)]
    line[-1] = c.note(7, 2) if rng.random() < 0.5 else line[-1]
    c.add(vib, 0.3, 0.4)
    c.add(resonant_lowpass(bass, 500, 0.8), 0.35, 0.5)
    c.add(glide(c.t, line) * np.minimum(1, c.t / 0.5), 0.25, 0.65)


def deep(c):
    rng = c.rng
    t = c.t
    c.add(np.sin(2 * np.pi * hz(c.root - 24) * t) + 0.5 * np.sin(2 * np.pi * hz(c.root - 12) * t), 0.45, 0.5)
    c.add(ensemble(c.chord(0, 0), c.n, "strings", 2.0, 1.5, rng), 0.25, 0.4)
    pings = np.zeros(c.n)
    for start in np.arange(rng.uniform(0.3, 1.0), c.seconds - 1, rng.uniform(2.5, 3.5)):
        m = int(1.5 * SR)
        tt = np.arange(m) / SR
        place(pings, start * SR, np.sin(2 * np.pi * rng.choice([700, 900, 1100]) * tt) * np.exp(-6 * tt))
    c.add(echo(pings, 0.5, 0.55, repeats=6), 0.2, float(rng.uniform(0.3, 0.7)))
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t)
    c.add(lowpass_noise(rng, c.n, 180) * swell, 0.3, 0.5)
    whale = [c.root + 12, c.root + 17, c.root + 10]
    c.add(glide(t, whale, 0.004) * np.clip(np.sin(np.pi * t / c.seconds) * 1.5, 0, 1), 0.12, 0.6)


# mood: (recipe, scales, bars, lowest root, highest root, ambient fades)
RECIPES = {
    "action": (action, ["phrygian", "minor"], 3, 40, 46, False),
    "heroic": (heroic, ["mixolydian", "major"], 2, 43, 50, False),
    "eerie":  (eerie, ["phrygian", "minor"], 2, 40, 47, True),
    "cosmic": (cosmic, ["lydian"], 2, 45, 53, True),
    "gentle": (gentle, ["major", "lydian"], 2, 48, 55, True),
    "neon":   (neon, ["minor", "dorian"], 3, 40, 46, False),
    "retro":  (retro, ["major", "mixolydian"], 2, 45, 52, False),
    "deep":   (deep, ["dorian", "minor"], 2, 38, 44, True),
}


def cue(path, seconds, seed, mood):
    """Write the cue for a mood; returns a short description."""
    fn, scales, bars, low, high, ambient = RECIPES[mood]
    c = Cue(seconds, seed, scales, bars, low, high)
    fn(c)
    c.write(path, *((0.4, 0.6) if ambient else (0.02, 0.2)))
    return f"{mood} cue, {c.mode} on {c.root}"
