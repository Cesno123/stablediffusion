"""Short film-score cues per picture mood (mood.py), so the music fits the motif.

Each mood has three clearly different variants (RECIPES), and music.pick() avoids
the cues of the last six posts, so the sound changes from post to post while it
still fits the picture. The first variant of each mood:
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
            sig = np.pad(sig[:self.n], (0, max(0, self.n - len(sig)))) / (np.abs(sig).max() + 1e-9) * gain
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


def epiano(n, midi, decay=1.8):
    """Warm electric piano (FM tine)."""
    t = np.arange(n) / SR
    f = hz(midi)
    mod = 1.2 * np.exp(-5 * t) * np.sin(2 * np.pi * f * t)
    return (np.sin(2 * np.pi * f * t + mod) + 0.2 * np.sin(4 * np.pi * f * t)) * np.exp(-decay * t) \
        * np.minimum(1, t / 0.004)



def choir(midis, n, rng, vowel="a"):
    """Soft 'aah' choir: detuned saws through two vowel formants."""
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        for d in (0.994, 1.0, 1.006):
            vib = 1 + 0.004 * np.sin(2 * np.pi * rng.uniform(4.5, 6) * t + rng.uniform(0, 6))
            x += saw(hz(m) * d * vib, t, 3500)
    f1, f2 = {"a": (750, 1150), "o": (450, 800), "u": (325, 700)}[vowel]
    low1 = resonant_lowpass(x, f1, 4.0)
    low2 = resonant_lowpass(x, f2, 4.0)
    out = low1 + 0.5 * (low2 - resonant_lowpass(x, f1 * 0.8, 1.0))
    return out * np.minimum(1, t / 0.8) * np.minimum(1, (n / SR - t) / 0.8)



def noise_hit(rng, n, bright=0.5, decay=20.0):
    """Clap / brush / shaker: filtered noise burst."""
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    x = x - np.convolve(x, np.ones(int(2 + 10 * (1 - bright))) / int(2 + 10 * (1 - bright)), mode="same")
    return x * np.exp(-decay * t)


def kick4(c, accents=(0, 4, 8, 12)):
    out = np.zeros(c.n)
    for b in range(c.bars):
        for i in accents:
            place(out, c.at(b, i), kick(int(0.35 * SR)))
    return out


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


# ---------------------------------------------- more recipes (variants per mood)

def action_pulse(c):
    """Driving synth: four-on-the-floor kick, pulsing octave bass, gated stabs (80s thriller)."""
    rng = c.rng
    prog = [0, 0, 5, 6][:c.bars] if c.bars <= 4 else [0, 5]
    bass, stabs = np.zeros(c.n), np.zeros(c.n)
    for b in range(c.bars):
        deg = prog[b % len(prog)]
        for i in range(0, 16, 1 if rng.random() < 0.5 else 2):
            m = c.note(deg) - 12 + (12 if i % 2 else 0)
            place(bass, c.at(b, i), voice("bass", m, int(c.step * 0.9 * SR), rng))
        for i in (0, 6, 10):
            place(stabs, c.at(b, i), ensemble(c.chord(deg, 1), int(c.step * 1.5 * SR), "brass", 0.005, 0.05, rng))
    hats = np.zeros(c.n)
    for b in range(c.bars):
        for i in range(2, 16, 4):
            place(hats, c.at(b, i), noise_hit(rng, int(0.1 * SR), 0.9, 40))
    c.add(kick4(c), 0.7, 0.5)
    c.add(bass, 0.5, 0.5)
    c.add(echo(stabs, c.step * 3, 0.3), 0.35, 0.6)
    c.add(hats, 0.15, 0.7)


def action_taiko(c):
    """Big drums in a rolling 6/8 feel with low string ostinato and a choir swell."""
    rng = c.rng
    drums, strings = np.zeros(c.n), np.zeros(c.n)
    pattern = [0, 3, 6, 8, 10, 12, 14] if rng.random() < 0.5 else [0, 2, 6, 8, 12, 13, 14]
    for b in range(c.bars):
        for k, i in enumerate(pattern):
            place(drums, c.at(b, i), timpani(int(0.9 * SR), c.root - 12 + (0 if k % 3 else 7), 1.0 if k == 0 else 0.6))
        for i in range(0, 16, 2):
            m = c.note([0, 0, 1, 0, 3, 2, 1, 0][i // 2]) - 12
            place(strings, c.at(b, i), ensemble([m], int(c.step * 2 * SR), "strings", 0.01, 0.05, rng))
    c.add(drums, 0.8, 0.5)
    c.add(strings, 0.45, 0.4)
    c.add(choir(c.chord(0, 1), c.n, rng, "o"), 0.25, 0.6)


def heroic_rise(c):
    """Rising strings over a snare roll, horns in fifths answering."""
    rng = c.rng
    strings, roll, horns = np.zeros(c.n), np.zeros(c.n), np.zeros(c.n)
    for b, deg in enumerate([0, int(rng.choice([4, 5, 6]))]):
        place(strings, c.at(b), ensemble(c.chord(deg, 1, 4), int(c.bar * SR), "strings", 0.5, 0.3, rng))
        place(horns, c.at(b, 8), ensemble([c.note(deg), c.note(deg + 4)], int(c.step * 8 * SR), "brass", 0.15, 0.3, rng))
    for k in range(int(c.seconds / 0.09)):
        place(roll, k * 0.09 * SR, noise_hit(rng, int(0.12 * SR), 0.7, 30) * (0.3 + 0.7 * k * 0.09 / c.seconds))
    c.add(strings, 0.5, 0.45)
    c.add(roll, 0.18, 0.55)
    c.add(echo(horns, c.step * 4, 0.2), 0.4, 0.6)
    c.add(timpani(int(1.5 * SR), c.root - 12, 1.0), 0.4, 0.5)


def heroic_choir(c):
    """Majestic organ and choir, a cathedral in space."""
    rng = c.rng
    organ, voices = np.zeros(c.n), np.zeros(c.n)
    for b, deg in enumerate([0, int(rng.choice([3, 5]))]):
        place(organ, c.at(b), ensemble(c.chord(deg, 0, 4) + [c.note(deg) - 12], int(c.bar * SR) + int(0.3 * SR), "organ", 0.3, 0.5, rng))
        place(voices, c.at(b), choir(c.chord(deg, 1), int(c.bar * SR) + int(0.3 * SR), rng, str(rng.choice(["a", "o"]))))
    c.add(organ, 0.45, 0.5)
    c.add(voices, 0.4, 0.5)
    c.add(echo(bell(int(3 * SR), c.note(7, 2), 1.0), 0.5, 0.4), 0.15, 0.7)


def eerie_musicbox(c):
    """A detuned, slowing music box over reversed swells: something is wrong here."""
    rng = c.rng
    box = np.zeros(c.n)
    notes = [c.note(int(d), 2) + (0.3 if rng.random() < 0.5 else 0) for d in rng.choice([0, 1, 3, 4, 6], size=6)]
    t_pos = 0.2
    for k, m in enumerate(notes):
        n = int(2.5 * SR)
        tt = np.arange(n) / SR
        f = 440.0 * 2 ** ((m - 69) / 12) * (1 - 0.01 * k)
        place(box, t_pos * SR, np.sin(2 * np.pi * f * tt) * np.exp(-3 * tt))
        t_pos += 0.45 + 0.12 * k  # slowing down like a dying spring
    swell = np.zeros(c.n)
    for start in (0.5, c.seconds / 2 + 0.3):
        n = int(2.2 * SR)
        place(swell, start * SR, ensemble([c.root + 12, c.root + 13], n, "strings", 0.01, 0.01, rng)[::-1])
    c.add(echo(box, 0.33, 0.45), 0.35, 0.65)
    c.add(swell, 0.3, 0.35)
    c.add(np.sin(2 * np.pi * hz(c.root - 12) * c.t), 0.25, 0.5)


def eerie_heartbeat(c):
    """Slow heartbeat, scraping metal and a low cluster: suspense."""
    rng = c.rng
    beat = np.zeros(c.n)
    period = c.seconds / int(rng.choice([6, 7, 8]))
    for k in range(int(c.seconds / period) + 1):
        for off, amp in ((0, 1.0), (0.22, 0.6)):
            place(beat, (k * period + off) * SR, kick(int(0.3 * SR)) * amp)
    scrape = np.zeros(c.n)
    for start in rng.uniform(0.5, c.seconds - 1.5, size=2):
        n = int(1.2 * SR)
        tt = np.arange(n) / SR
        f = rng.uniform(900, 2400) * (1 + 0.15 * np.sin(2 * np.pi * 3 * tt))
        place(scrape, start * SR, np.sin(2 * np.pi * np.cumsum(f) / SR) * rng.normal(1, 0.4, n) * np.sin(np.pi * tt / tt[-1]))
    c.add(beat, 0.6, 0.5)
    c.add(echo(scrape, 0.4, 0.4), 0.12, float(rng.uniform(0.2, 0.8)))
    c.add(ensemble([c.root, c.root + 1, c.root + 6], c.n, "strings", 2.0, 1.5, rng), 0.3, 0.45)



def cosmic_choir(c):
    """Distant choir and a sub drone: the silence of deep space, but human."""
    rng = c.rng
    c.add(choir(c.chord(0, 1), c.n, rng, str(rng.choice(["a", "o", "u"]))), 0.45, 0.45)
    c.add(choir([c.note(4, 2)], c.n, rng, "u"), 0.15, 0.7)
    c.add(np.sin(2 * np.pi * hz(c.root - 24) * c.t) + 0.3 * np.sin(2 * np.pi * hz(c.root - 12) * c.t), 0.3, 0.5)
    sparkle = np.zeros(c.n)
    for start in rng.uniform(0.5, c.seconds - 1, size=int(rng.integers(3, 6))):
        place(sparkle, start * SR, bell(int(2 * SR), c.note(int(rng.choice([0, 2, 4, 6])), 3), 2.0))
    c.add(echo(sparkle, 0.45, 0.5, repeats=5), 0.12, float(rng.uniform(0.2, 0.8)))


def gentle_epiano(c):
    """Warm electric piano chords with soft brushes: a calm evening."""
    rng = c.rng
    keys, brush, bass = np.zeros(c.n), np.zeros(c.n), np.zeros(c.n)
    for b, deg in enumerate([0, int(rng.choice([3, 5]))]):
        for i in (0, 6, 8) if rng.random() < 0.5 else (0, 8):
            for m in c.chord(deg, 1, 4):
                place(keys, c.at(b, i), epiano(int(2.2 * SR), m))
        place(bass, c.at(b), voice("bass", c.note(deg) - 12, int(c.bar * SR), rng))
        for i in range(0, 16, 4):
            place(brush, c.at(b, i + 2), noise_hit(rng, int(0.2 * SR), 0.6, 14))
    c.add(keys, 0.45, 0.5)
    c.add(resonant_lowpass(bass, 350, 0.7), 0.3, 0.5)
    c.add(brush, 0.08, 0.6)



def neon_dark(c):
    """Slow dark synth with rain: a lonely street at night."""
    rng = c.rng
    c.add(ensemble(c.chord(0, 1), c.n, "brass", 1.0, 1.0, rng), 0.35, 0.4)
    bass = np.zeros(c.n)
    for b in range(c.bars):
        place(bass, c.at(b), voice("bass", c.note(0) - 12, int(c.bar * SR), rng))
    c.add(bass, 0.35, 0.5)
    c.add(noise_hit(rng, c.n, 0.95, 0.0) * 0.5, 0.08, 0.5)  # rain
    snare_line = np.zeros(c.n)
    for b in range(c.bars):
        place(snare_line, c.at(b, 8), snare(rng, int(0.4 * SR)))
    c.add(echo(snare_line, c.step * 6, 0.45), 0.3, 0.5)


def neon_funk(c):
    """Electro funk: syncopated bass, claps and short chord stabs."""
    rng = c.rng
    bass, claps, stabs = np.zeros(c.n), np.zeros(c.n), np.zeros(c.n)
    line = [0, 3, 6, 10, 11, 14]
    for b in range(c.bars):
        for k, i in enumerate(line):
            m = c.note([0, 0, 2, 0, 4, 3][k]) - 12
            place(bass, c.at(b, i), voice("bass", m, int(c.step * 1.5 * SR), rng))
        for i in (4, 12):
            place(claps, c.at(b, i), noise_hit(rng, int(0.2 * SR), 0.7, 25))
        place(stabs, c.at(b, 7), ensemble(c.chord(0, 1, 4), int(c.step * 1.2 * SR), "strings", 0.005, 0.05, rng))
    c.add(kick4(c, (0, 8)), 0.6, 0.5)
    c.add(bass, 0.5, 0.5)
    c.add(claps, 0.3, 0.55)
    c.add(echo(stabs, c.step * 3, 0.35), 0.3, 0.6)


def retro_lounge(c):
    """Space-age bachelor pad: swinging hats, walking bass, vibraphone chords."""
    rng = c.rng
    vib, bass, hats = np.zeros(c.n), np.zeros(c.n), np.zeros(c.n)
    for b, deg in enumerate([0, 3]):
        for i in (0, 10):
            for m in c.chord(deg, 1, 4):
                place(vib, c.at(b, i), vibes(int(1.4 * SR), m))
        for k, i in enumerate((0, 4, 8, 12)):
            place(bass, c.at(b, i), voice("bass", c.note(deg + [0, 2, 4, 6][k]) - 12, int(c.step * 3.6 * SR), rng))
        for i in (0, 4, 7, 8, 12, 15):  # swung ride
            place(hats, c.at(b, i), noise_hit(rng, int(0.25 * SR), 0.95, 12))
    c.add(vib, 0.35, 0.4)
    c.add(resonant_lowpass(bass, 500, 0.8), 0.35, 0.5)
    c.add(hats, 0.1, 0.65)



def deep_whales(c):
    """Whale song glides over low strings and drifting bubbles."""
    rng = c.rng
    t = c.t
    calls = [c.root + 12 + int(x) for x in rng.choice([0, 3, 5, 7, 10, -2], size=4)]
    c.add(glide(t, calls, 0.006) * (0.5 + 0.5 * np.sin(np.pi * t / c.seconds)), 0.2, 0.6)
    c.add(ensemble([c.root - 12, c.root - 5, c.root], c.n, "strings", 2.0, 2.0, rng), 0.35, 0.45)
    bubbles = np.zeros(c.n)
    for start in rng.uniform(0.2, c.seconds - 0.3, size=int(rng.integers(8, 16))):
        n = int(0.08 * SR)
        tt = np.arange(n) / SR
        f = rng.uniform(400, 1200) * (1 + 3 * tt / tt[-1])
        place(bubbles, start * SR, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-30 * tt))
    c.add(bubbles, 0.12, float(rng.uniform(0.3, 0.7)))
    c.add(lowpass_noise(rng, c.n, 150), 0.25, 0.5)


def deep_engine(c):
    """Inside a submarine: engine hum pulsing, hull creaks, a far sonar."""
    rng = c.rng
    t = c.t
    hum = (np.sin(2 * np.pi * hz(c.root - 24) * t) + 0.5 * np.sin(2 * np.pi * hz(c.root - 12) * 1.01 * t)) \
        * (0.6 + 0.4 * np.sin(2 * np.pi * (c.bars / c.seconds) * 2 * t))
    c.add(hum, 0.45, 0.5)
    creak = np.zeros(c.n)
    for start in rng.uniform(0.5, c.seconds - 1, size=2):
        n = int(0.6 * SR)
        tt = np.arange(n) / SR
        f = rng.uniform(80, 200) * (1 + 0.3 * np.sin(2 * np.pi * 7 * tt))
        place(creak, start * SR, saw(f, tt, 1500) * np.sin(np.pi * tt / tt[-1]))
    c.add(resonant_lowpass(creak, 600, 3.0), 0.15, float(rng.uniform(0.2, 0.8)))
    ping = np.zeros(c.n)
    place(ping, rng.uniform(0.5, 2.0) * SR, np.sin(2 * np.pi * 1000 * np.arange(int(1.2 * SR)) / SR) * np.exp(-5 * np.arange(int(1.2 * SR)) / SR))
    c.add(echo(ping, 0.6, 0.6, repeats=6), 0.15, 0.7)
    c.add(ensemble(c.chord(0, 0), c.n, "strings", 2.0, 2.0, rng), 0.2, 0.4)


# ------------------------------------------- soundscapes: no melody, no beat, just a place

def wind(c, cutoff=600, speed=0.08, depth=0.5):
    return lowpass_noise(c.rng, c.n, cutoff) * (1 - depth + depth * np.sin(2 * np.pi * speed * c.t + c.rng.uniform(0, 6)))


def rumble(c, cutoff=90):
    return lowpass_noise(c.rng, c.n, cutoff) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.05 * c.t))


def events(c, count, make, spread=(0.3, 0.9)):
    """count one-off sounds made by make(rng) at random times, each with its own place in the stereo field."""
    out = np.zeros(c.n)
    for start in c.rng.uniform(0.2, c.seconds - 0.5, size=count):
        place(out, start * SR, make(c.rng))
    return out


def chirp(rng, f0, f1, length, decay):
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (tt / tt[-1])
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-decay * tt) * np.minimum(1, tt / 0.005)


def boom(rng):
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    return lowpass_noise(rng, n, rng.uniform(80, 200)) * np.exp(-2.5 * tt) * np.minimum(1, tt / 0.02)


# ------------------------------------------ targeted sounds for a soundscape (chosen by Claude)

def _sfx_pulses(c, period, make, jitter=0.2):
    out = np.zeros(c.n)
    t0 = c.rng.uniform(0, period)
    while t0 < c.seconds:
        place(out, t0 * SR, make())
        t0 += period * c.rng.uniform(1 - jitter, 1 + jitter)
    return out


def _sound(c, name):
    """(signal, gain) for one named sound effect."""
    rng, t, n = c.rng, c.t, c.n
    if name == "wind":
        return wind(c, 600, 0.08, 0.6), 0.35
    if name == "rain":
        return noise_hit(rng, n, 0.95, 0.0) + 0.5 * lowpass_noise(rng, n, 3000), 0.18
    if name == "thunder":
        return events(c, 1, lambda r: lowpass_noise(r, int(4 * SR), 120) * np.exp(-0.9 * np.arange(int(4 * SR)) / SR)
                      * np.minimum(1, np.arange(int(4 * SR)) / (0.15 * SR))), 0.5
    if name == "waves":
        return lowpass_noise(rng, n, 900) * (0.3 + 0.7 * np.sin(np.pi * ((t / 3.2) % 1)) ** 2), 0.35
    if name == "stream":
        return lowpass_noise(rng, n, 2500) * (0.8 + 0.2 * np.sin(2 * np.pi * 3.1 * t)), 0.15
    if name == "lava":
        bubbles = events(c, int(rng.integers(10, 18)), lambda r: chirp(r, r.uniform(60, 140), r.uniform(150, 300), 0.18, 12))
        return bubbles + 0.5 * rumble(c, 80), 0.4
    if name == "fire":
        return events(c, int(rng.integers(25, 45)), lambda r: noise_hit(r, int(0.04 * SR), 0.9, 120)) \
            + 0.4 * lowpass_noise(rng, n, 500), 0.2
    if name == "engine":
        f = hz(c.root - 24) * (1 + 0.02 * np.sin(2 * np.pi * 0.3 * t))
        return resonant_lowpass(saw(f, t, 1200), 300, 1.5) * (0.8 + 0.2 * np.sin(2 * np.pi * 9 * t)), 0.35
    if name == "thrusters":
        return lowpass_noise(rng, n, 1500) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * t)) + 0.4 * rumble(c, 90), 0.4
    if name == "ship hum":
        return (np.sin(2 * np.pi * hz(c.root - 24) * t) + 0.5 * np.sin(2 * np.pi * hz(c.root - 17) * t)) \
            * (0.75 + 0.25 * np.sin(2 * np.pi * 0.5 * t)), 0.35
    if name == "radio":
        def burst(r):  # a few words of crackling voice
            n = int(r.uniform(0.3, 0.9) * SR)
            gate = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * r.uniform(4, 9) * np.arange(n) / SR))
            return resonant_lowpass(r.normal(0, 1, n) * gate, 1800, 3.0)
        chatter = events(c, int(rng.integers(3, 6)), burst)
        return chatter + 0.3 * events(c, 2, lambda r: chirp(r, 1400, 1400, 0.12, 8)), 0.12
    if name == "computers":
        beep = lambda r: np.sin(2 * np.pi * r.choice([700, 900, 1200, 1500, 1800]) * np.arange(int(0.08 * SR)) / SR)  # noqa: E731
        return events(c, int(rng.integers(8, 16)), beep) + 0.3 * np.sin(2 * np.pi * 120 * t), 0.08
    if name == "crowd":
        x = sum(resonant_lowpass(rng.normal(0, 1, n), rng.uniform(300, 900), 4.0) * (0.6 + 0.4 * np.sin(
            2 * np.pi * rng.uniform(0.2, 0.7) * t + rng.uniform(0, 6))) for _ in range(3))
        return x, 0.2
    if name == "footsteps":
        step = lambda: noise_hit(rng, int(0.12 * SR), 0.5, 35)  # noqa: E731
        return _sfx_pulses(c, rng.uniform(0.45, 0.6), step, 0.08), 0.25
    if name == "wheels":
        return lowpass_noise(rng, n, 400) * (0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 6 * t))) \
            + 0.6 * _sfx_pulses(c, 0.35, lambda: noise_hit(rng, int(0.06 * SR), 0.4, 50), 0.4), 0.3
    if name == "birds":
        return events(c, int(rng.integers(4, 8)), lambda r: chirp(r, r.uniform(2000, 3500), r.uniform(3000, 5000),
                                                                   r.uniform(0.08, 0.2), 12)), 0.1
    if name == "insects":
        return lowpass_noise(rng, n, 6000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 30 * t))) \
            * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t)), 0.05
    if name == "creature":
        return events(c, int(rng.integers(1, 3)), lambda r: resonant_lowpass(saw(
            r.uniform(55, 90) * (1 + 0.3 * np.sin(np.pi * np.arange(int(1.6 * SR)) / int(1.6 * SR))),
            np.arange(int(1.6 * SR)) / SR, 1500), 500, 4.0) * np.sin(np.pi * np.arange(int(1.6 * SR)) / int(1.6 * SR))), 0.3
    if name == "creaks":
        return events(c, 2, lambda r: resonant_lowpass(saw(r.uniform(60, 120) * (1 + 0.2 * np.sin(2 * np.pi * 6 * np.arange(
            int(0.8 * SR)) / SR)), np.arange(int(0.8 * SR)) / SR, 1200), 500, 3.0) * np.sin(np.pi * np.arange(int(0.8 * SR))
            / int(0.8 * SR))), 0.18
    if name == "drips":
        return echo(events(c, int(rng.integers(4, 8)), lambda r: chirp(r, r.uniform(1500, 2500), r.uniform(600, 900),
                                                                        0.06, 40)), 0.35, 0.5), 0.15
    if name == "alarm":
        return np.sin(2 * np.pi * (600 + 250 * np.sin(2 * np.pi * 0.5 * t)) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)), 0.06
    if name == "explosions":
        return events(c, int(rng.integers(2, 4)), boom), 0.45
    if name == "sonar":
        ping = np.zeros(n)
        place(ping, rng.uniform(0.5, 2) * SR, chirp(rng, 900, 900, 1.2, 4))
        return echo(ping, 0.7, 0.55, repeats=6), 0.12
    if name == "electricity":
        zap = lambda r: resonant_lowpass(r.normal(0, 1, int(0.15 * SR)) * np.exp(-20 * np.arange(int(0.15 * SR)) / SR),
                                         r.uniform(2000, 5000), 3.0)  # noqa: E731
        return events(c, int(rng.integers(4, 9)), zap) + 0.2 * (np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 300 * t)), 0.2
    if name == "bubbles":
        return events(c, int(rng.integers(8, 15)), lambda r: chirp(r, r.uniform(300, 700), r.uniform(900, 1800), 0.07, 30)), 0.12
    return np.zeros(n), 0.0


SOUNDS = ["wind", "rain", "thunder", "waves", "stream", "lava", "fire", "engine", "thrusters", "ship hum", "radio",
          "computers", "crowd", "footsteps", "wheels", "birds", "insects", "creature", "creaks", "drips", "alarm",
          "explosions", "sonar", "electricity", "bubbles"]


def soundscape(c):
    """A pure sound environment for the picture's mood (c.mood): air, machines, water, signals."""
    rng, t, mood = c.rng, c.t, c.mood
    chosen = [x for x in getattr(c, "sounds", []) if x in SOUNDS]
    if chosen:  # the sounds Claude heard in the picture, over a quiet bed of air
        c.add(lowpass_noise(rng, c.n, 400) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.06 * t)), 0.12, 0.5)
        for x in chosen[:4]:
            sig, gain = _sound(c, x)
            c.add(sig, gain, float(rng.uniform(0.25, 0.75)))
        return
    drone = np.sin(2 * np.pi * hz(c.root - 24) * t) + 0.4 * np.sin(2 * np.pi * hz(c.root - 12) * 1.003 * t)
    if mood == "action":  # a battle far away: rumble, distant blasts, an alarm sweeping
        c.add(rumble(c, 70), 0.5, 0.5)
        c.add(events(c, int(rng.integers(3, 6)), boom), 0.45, 0.4)
        alarm = np.sin(2 * np.pi * (600 + 250 * np.sin(2 * np.pi * 0.5 * t)) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t))
        c.add(resonant_lowpass(alarm, 1200, 1.0), 0.06, 0.7)
    elif mood == "heroic":  # a launch pad: deep engine roar slowly rising, wind, radio blips
        roar = lowpass_noise(rng, c.n, 140) * np.minimum(1, 0.3 + t / c.seconds)
        c.add(roar, 0.55, 0.5)
        c.add(wind(c, 900, 0.1), 0.2, 0.5)
        c.add(events(c, 3, lambda r: chirp(r, 1200, 1200, 0.12, 10)), 0.08, 0.75)
    elif mood == "eerie":  # a derelict: drips, creaking metal, breathing air
        c.add(drone, 0.25, 0.5)
        c.add(echo(events(c, int(rng.integers(4, 8)), lambda r: chirp(r, r.uniform(1500, 2500), r.uniform(600, 900), 0.06, 40)), 0.35, 0.5), 0.15, 0.4)
        c.add(events(c, 2, lambda r: resonant_lowpass(saw(r.uniform(60, 120) * (1 + 0.2 * np.sin(2 * np.pi * 6 * np.arange(int(0.8 * SR)) / SR)), np.arange(int(0.8 * SR)) / SR, 1200), 500, 3.0) * np.sin(np.pi * np.arange(int(0.8 * SR)) / int(0.8 * SR))), 0.18, 0.6)
        c.add(wind(c, 400, 0.15, 0.8), 0.2, 0.5)
    elif mood == "cosmic":  # deep space: solar wind, a low hum, a pulsar ticking far away
        c.add(wind(c, 500, 0.05), 0.35, 0.5)
        c.add(drone, 0.3, 0.5)
        ticks = np.zeros(c.n)
        period = rng.uniform(0.6, 1.2)
        for k in range(int(c.seconds / period)):
            place(ticks, k * period * SR, chirp(rng, 2000, 2000, 0.03, 80))
        c.add(echo(ticks, period / 2, 0.3), 0.06, 0.7)
    elif mood == "gentle":  # a quiet planet morning: breeze, water, strange small birds
        c.add(wind(c, 1200, 0.12, 0.6), 0.25, 0.5)
        c.add(lowpass_noise(rng, c.n, 2500) * 0.4, 0.1, 0.4)  # a stream
        c.add(events(c, int(rng.integers(4, 7)), lambda r: chirp(r, r.uniform(2000, 3500), r.uniform(3000, 5000), r.uniform(0.08, 0.2), 12)), 0.1, 0.65)
    elif mood == "neon":  # a city night: rain, traffic hum, neon buzz, a hover car passing
        c.add(noise_hit(rng, c.n, 0.95, 0.0), 0.12, 0.5)
        c.add(np.sin(2 * np.pi * 50 * t) + 0.3 * np.sin(2 * np.pi * 150 * t), 0.06, 0.6)
        c.add(rumble(c, 120), 0.3, 0.5)
        start = rng.uniform(1, c.seconds - 3)
        whoosh = lowpass_noise(rng, c.n, 900) * np.exp(-((t - start - 1) / 0.6) ** 2)
        c.add(whoosh, 0.3, float(rng.uniform(0.2, 0.8)))
    elif mood == "retro":  # a 1950s control room: valve hum, relay clicks, computer beeps
        c.add(np.sin(2 * np.pi * 60 * t) + 0.3 * np.sin(2 * np.pi * 120 * t), 0.15, 0.5)
        c.add(events(c, int(rng.integers(6, 12)), lambda r: noise_hit(r, int(0.03 * SR), 0.9, 200)), 0.12, 0.4)
        beep = lambda r: np.sin(2 * np.pi * r.choice([800, 1000, 1200, 1600]) * np.arange(int(0.12 * SR)) / SR)  # noqa: E731
        c.add(events(c, int(rng.integers(3, 6)), beep), 0.07, 0.65)
        c.add(lowpass_noise(rng, c.n, 3000) * 0.3, 0.05, 0.5)  # tape hiss
    else:  # deep: under water, low pressure, bubbles, a far sonar
        c.add(rumble(c, 110), 0.45, 0.5)
        c.add(events(c, int(rng.integers(8, 15)), lambda r: chirp(r, r.uniform(300, 700), r.uniform(900, 1800), 0.07, 30)), 0.1, 0.55)
        ping = np.zeros(c.n)
        place(ping, rng.uniform(0.5, 2) * SR, chirp(rng, 900, 900, 1.2, 4))
        c.add(echo(ping, 0.7, 0.55, repeats=6), 0.1, 0.7)


# ------------------------------------------------- scenes the first moods did not cover

def wasteland(c):
    """Lonely frontier: a slow bending twang over wind and a low drone (desert, dunes, wasteland)."""
    rng, t = c.rng, c.t
    c.add(wind(c, 700, 0.07, 0.6), 0.3, 0.5)
    c.add(np.sin(2 * np.pi * hz(c.root - 12) * t) + 0.3 * np.sin(2 * np.pi * hz(c.root - 5) * t), 0.25, 0.5)
    twang = np.zeros(c.n)
    for k, start in enumerate(sorted(rng.uniform(0.3, c.seconds - 2.5, size=3))):
        n = int(2.5 * SR)
        tt = np.arange(n) / SR
        f = hz(c.note(int(rng.choice([0, 2, 4, 7])), 1)) * (1 - 0.02 * np.minimum(1, tt / 0.6))  # sliding down
        x = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) * np.exp(-2.5 * h * tt) / h for h in range(1, 6))
        place(twang, start * SR, x * np.minimum(1, tt / 0.003))
    c.add(echo(twang, 0.55, 0.45, repeats=5), 0.3, 0.6)


def machines(c):
    """Industry at work: a slow mechanical rhythm, hydraulic hiss, an engine drone; no melody."""
    rng, t = c.rng, c.t
    clank = np.zeros(c.n)
    pattern = [0, 6, 8, 14] if rng.random() < 0.5 else [0, 3, 8, 11]
    for b in range(c.bars):
        for i in pattern:
            n = int(0.35 * SR)
            tt = np.arange(n) / SR
            hit = np.sin(2 * np.pi * rng.uniform(180, 420) * tt) * np.sin(2 * np.pi * rng.uniform(900, 1800) * tt)
            place(clank, c.at(b, i), (hit * np.exp(-14 * tt) + 0.6 * noise_hit(rng, n, 0.6, 30)))
    c.add(clank, 0.45, 0.45)
    hiss = np.zeros(c.n)
    for start in rng.uniform(0.5, c.seconds - 1.5, size=2):
        n = int(1.2 * SR)
        place(hiss, start * SR, lowpass_noise(rng, n, 4000) * np.sin(np.pi * np.arange(n) / n))
    c.add(hiss, 0.15, float(rng.uniform(0.2, 0.8)))
    c.add((np.sin(2 * np.pi * hz(c.root - 24) * t) + 0.5 * np.sin(2 * np.pi * hz(c.root - 12) * t))
          * (0.7 + 0.3 * np.sin(2 * np.pi * (c.bars / c.seconds) * t)), 0.4, 0.5)


def lament(c):
    """Melancholy: slow minor strings and a few lonely piano notes (ruins, loss, a lone figure)."""
    rng = c.rng
    pads = np.zeros(c.n)
    for b, deg in enumerate([0, int(rng.choice([5, 3]))]):
        place(pads, c.at(b), ensemble(c.chord(deg, 0, 3), int(c.bar * SR) + int(0.4 * SR), "strings", 1.2, 1.0, rng))
    keys = np.zeros(c.n)
    for k, step in enumerate(sorted(rng.choice([2, 6, 10, 18, 22, 26], size=3, replace=False))):
        deg = 7 if k == 2 else int(rng.choice([2, 4, 5]))
        place(keys, c.at(0, int(step)), epiano(int(3 * SR), c.note(deg, 1), 1.2))
    c.add(pads, 0.45, 0.45)
    c.add(echo(keys, c.step * 5, 0.35), 0.3, 0.6)


def temple(c):
    """Ancient and mystical: singing bowls, a low chant and a rare deep drum (temples, relics, alien shrines)."""
    rng, t = c.rng, c.t
    bowls = np.zeros(c.n)
    for start in sorted(rng.uniform(0.2, c.seconds - 3, size=2)):
        n = int(5 * SR)
        tt = np.arange(n) / SR
        f = hz(c.note(int(rng.choice([0, 4])), 1))
        x = sum(np.sin(2 * np.pi * f * r * tt) * np.exp(-d * tt) for r, d in ((1, 0.6), (2.76, 1.2), (5.4, 2.5)))
        place(bowls, start * SR, x * (1 + 0.1 * np.sin(2 * np.pi * 4 * tt)) * np.minimum(1, tt / 0.01))
    c.add(bowls, 0.3, 0.55)
    c.add(choir([c.root, c.root + 7], c.n, rng, "u"), 0.35, 0.45)
    drum = np.zeros(c.n)
    place(drum, c.at(0), timpani(int(2 * SR), c.root - 12, 1.0))
    c.add(drum, 0.3, 0.5)


# ------------------------------------------------------- melodies: singable, new every time

RHYTHMS = [  # note lengths in beats over eight beats (two bars of four); 0 = a rest of one beat
    [2, 1, 1, 2, 2], [1.5, 0.5, 2, 1, 1, 2], [3, 1, 2, 2], [1, 1, 2, 1, 1, 2], [2, 2, 1, 1, 2],
    [0, 1, 1, 2, 2, 2], [1.5, 0.5, 1, 1, 3, 1], [2, 1.5, 0.5, 4], [1, 2, 1, 2, 2], [0, 2, 1, 1, 1, 3],
]
CONTOURS = ["arch", "rise", "fall", "wave", "valley"]
# lead instruments that suit each mood (a melody picks one at random)
LEADS = {
    "action": ["brass", "synth", "strings"], "heroic": ["brass", "strings", "flute"],
    "eerie": ["theremin", "whistle", "bell"], "cosmic": ["flute", "strings", "synth", "bell", "whistle"],
    "gentle": ["flute", "epiano", "bell", "whistle"], "neon": ["synth", "epiano", "reed"],
    "retro": ["theremin", "vibes", "brass", "whistle"], "deep": ["flute", "theremin", "strings"],
    "frontier": ["whistle", "reed", "flute"], "industry": ["brass", "synth"],
    "sorrow": ["strings", "epiano", "flute"], "ancient": ["flute", "reed", "strings"],
}


def lead(kind, midi, n, rng):
    """One melody note."""
    t = np.arange(n) / SR
    f = hz(midi)
    vib = 1 + 0.008 * np.minimum(1, np.maximum(0, t - 0.25) / 0.4) * np.sin(2 * np.pi * rng.uniform(4.8, 5.8) * t)
    env = np.minimum(1, t / 0.06) * np.minimum(1, np.maximum(0, (n / SR - t) / 0.15))
    if kind == "flute":
        phase = 2 * np.pi * np.cumsum(f * vib) / SR
        breath = lowpass_noise(rng, n, 3000) * 0.06
        return (np.sin(phase) + 0.15 * np.sin(2 * phase) + 0.05 * np.sin(3 * phase) + breath) * env
    if kind == "whistle":
        return np.sin(2 * np.pi * np.cumsum(f * vib) / SR) * env
    if kind == "reed":
        phase = 2 * np.pi * np.cumsum(f * vib) / SR
        return resonant_lowpass(np.sign(np.sin(phase) + 0.3) * 0.5, 1800, 1.2) * env
    if kind == "synth":
        x = saw(f * vib, t, 5000)
        return resonant_lowpass(x, 600 + 2400 * np.exp(-4 * t), 2.0) * env
    if kind == "strings":
        return ensemble([midi], n, "strings", 0.15, 0.2, rng)
    if kind == "epiano":
        return epiano(n, midi, 1.5)
    if kind == "bell":
        return bell(n, midi, 1.5)
    if kind == "vibes":
        return vibes(n, midi)
    return voice(kind, midi, n, rng)  # brass, theremin


LEAD_KINDS = ["flute", "whistle", "reed", "synth", "strings", "epiano", "bell", "vibes", "brass", "theremin"]


def melody(c, seed, kind=None, contour=None):
    """A short singable line: a fresh rhythm and note sequence per seed, chord tones on the strong
    beats, steps in between, ending on the root or fifth so the reel loops. kind and contour come
    from Claude (what suits the picture); without them they are picked to suit the mood."""
    rng = np.random.default_rng(seed + 7919)
    kind = kind if kind in LEAD_KINDS else str(rng.choice(LEADS.get(c.mood, ["flute", "strings"])))
    rhythm = list(RHYTHMS[int(rng.integers(len(RHYTHMS)))])
    contour = contour if contour in CONTOURS else str(rng.choice(CONTOURS))
    beat = c.seconds / 8
    count = sum(1 for d in rhythm if d)
    octave = 1 if kind in ("strings", "brass", "reed") else int(rng.choice([1, 2]))
    deg = int(rng.choice([0, 2, 4]))
    out = np.zeros(c.n)
    pos, k = 0.0, 0
    for d in rhythm:
        if d == 0:  # a rest
            pos += 1
            continue
        x = k / max(1, count - 1)
        target = {"arch": 4 * (1 - abs(2 * x - 1)), "rise": 5 * x, "fall": 5 * (1 - x),
                  "wave": 2 + 2 * np.sin(2 * np.pi * x), "valley": 4 * abs(2 * x - 1)}[contour]
        if k == count - 1:
            deg = int(rng.choice([0, 4, 7]))  # land on the root or fifth
        else:
            deg += int(np.clip(round(target) - deg, -2, 2)) + int(rng.choice([0, 0, 1, -1]))
            if pos % 2 == 0 and deg % 2:  # strong beats prefer chord tones
                deg += int(rng.choice([-1, 1]))
        n = int(d * beat * SR * 0.97)
        place(out, pos * beat * SR, lead(kind, c.note(deg, octave), n, rng))
        pos += d
        k += 1
    return echo(out, beat * float(rng.choice([0.75, 1.5])), float(rng.uniform(0.15, 0.35))), kind


# mood: list of (variant, recipe, scales, bars, lowest root, highest root, ambient fades).
# Several clearly different variants per mood keep the music varied while it fits the picture.
RECIPES = {
    "action": [("war drums", action, ["phrygian", "minor"], 3, 40, 46, False),
               ("synth pulse", action_pulse, ["minor", "phrygian"], 4, 40, 46, False),
               ("taiko", action_taiko, ["phrygian", "minor"], 2, 40, 45, False),
               ("soundscape", soundscape, ["minor"], 2, 40, 46, True)],
    "heroic": [("brass", heroic, ["mixolydian", "major"], 2, 43, 50, False),
               ("rising strings", heroic_rise, ["major", "lydian"], 2, 43, 50, False),
               ("cathedral", heroic_choir, ["major", "mixolydian"], 2, 41, 48, True),
               ("soundscape", soundscape, ["major"], 2, 40, 46, True)],
    "eerie":  [("cluster", eerie, ["phrygian", "minor"], 2, 40, 47, True),
               ("music box", eerie_musicbox, ["minor", "phrygian"], 2, 45, 52, True),
               ("heartbeat", eerie_heartbeat, ["phrygian"], 2, 38, 45, True),
               ("soundscape", soundscape, ["phrygian"], 2, 38, 45, True)],
    "cosmic": [("strings", cosmic, ["lydian"], 2, 45, 53, True),
               ("soundscape", soundscape, ["lydian"], 2, 40, 47, True),
               ("choir", cosmic_choir, ["lydian", "major", "dorian"], 2, 43, 50, True)],
    "gentle": [("music box", gentle, ["major", "lydian"], 2, 48, 55, True),
               ("e-piano", gentle_epiano, ["major", "mixolydian", "dorian"], 2, 45, 52, True),
               ("soundscape", soundscape, ["major"], 2, 45, 52, True)],
    "neon":   [("synthwave", neon, ["minor", "dorian"], 3, 40, 46, False),
               ("dark rain", neon_dark, ["minor", "phrygian"], 2, 40, 46, True),
               ("electro funk", neon_funk, ["dorian", "minor"], 4, 40, 46, False),
               ("soundscape", soundscape, ["minor"], 2, 40, 46, True)],
    "retro":  [("vibes", retro, ["major", "mixolydian"], 2, 45, 52, False),
               ("lounge", retro_lounge, ["major", "dorian"], 2, 43, 50, False),
               ("soundscape", soundscape, ["major"], 2, 45, 52, True)],
    "deep":   [("sonar", deep, ["dorian", "minor"], 2, 38, 44, True),
               ("whales", deep_whales, ["dorian", "lydian"], 2, 40, 46, True),
               ("engine", deep_engine, ["minor", "phrygian"], 2, 38, 44, True),
               ("soundscape", soundscape, ["dorian"], 2, 38, 44, True)],
    "frontier": [("wasteland", wasteland, ["dorian", "minor"], 2, 40, 47, True)],
    "industry": [("machines", machines, ["minor", "phrygian"], 2, 38, 44, False)],
    "sorrow":   [("lament", lament, ["minor", "dorian"], 2, 43, 50, True)],
    "ancient":  [("temple", temple, ["phrygian", "dorian"], 2, 40, 46, True)],
}

# What picture each cue fits; Claude reads this list and picks the cues for a picture (mood.py).
FITS = {
    "action:war_drums": "a battle or attack in full swing, warships firing, invasion",
    "action:synth_pulse": "a fast chase or escape, racing ships or vehicles, tense high-tech pursuit",
    "action:taiko": "an epic clash of giants, colossal monsters or armies, raw ancient-feeling power",
    "action:soundscape": "the aftermath or a battle far away: wreckage, smoke on the horizon, burning ships",
    "heroic:brass": "a triumphant launch, a proud fleet, victory, a hero ship in its glory",
    "heroic:rising_strings": "departure and hope: a ship rising into the sky, an expedition setting out",
    "heroic:cathedral": "monumental, almost sacred scale: colossal stations, megastructures, awe-inspiring architecture",
    "heroic:soundscape": "raw machine power before takeoff: a launch pad, engines firing up, a shipyard",
    "eerie:cluster": "an alien threat or dark mystery, strange creatures, the unknown",
    "eerie:music_box": "abandoned human places, an empty colony, a haunted home, nostalgic decay",
    "eerie:heartbeat": "suspense: a lone figure in danger, hiding, something approaching",
    "eerie:soundscape": "inside a derelict, ruins, caves, wrecks, dripping darkness",
    "cosmic:strings": "a serene space vista, planets and nebulae, quiet wonder",
    "cosmic:choir": "the sublime cosmos: vast light, huge celestial bodies, humans tiny before the universe",
    "cosmic:soundscape": "empty silent space: a lone probe or station, a cold void, nothing moving",
    "gentle:music_box": "dreamy, small and cozy: children, toys, a little house under alien skies",
    "gentle:e-piano": "relaxed everyday life: people at ease, a café, a warm evening, a living room",
    "gentle:soundscape": "peaceful nature on another world: meadows, gardens, water, morning light",
    "neon:synthwave": "night drive through a neon city, cool 80s retro-future streets",
    "neon:dark_rain": "lonely rainy noir: a detective, a melancholy figure in the city at night",
    "neon:electro_funk": "lively nightlife: crowds, clubs, markets, a buzzing fun city",
    "neon:soundscape": "a city at night with no one in focus: rainy streets, traffic, skyline",
    "retro:vibes": "playful 1950s/60s futurism: rockets on fins, flying saucers, ray guns, tin robots",
    "retro:lounge": "space-age leisure and style: a retro lounge, hotel, fashion, cocktails on the moon",
    "retro:soundscape": "a retro control room: mainframe computers, labs, mission control, blinking panels",
    "deep:sonar": "underwater exploration: a submarine in the deep, dark ocean",
    "deep:whales": "sea creatures and ocean life: whales, giant animals, a living deep sea",
    "deep:engine": "inside a submarine or ship hull, an industrial underwater base",
    "deep:soundscape": "under water or under ice: frozen silence, depths with nothing happening",
    "frontier:wasteland": "a lonely frontier: deserts, dunes, wasteland, a lone rover or traveller, wide empty land",
    "industry:machines": "industry at work: mining, factories, cranes, cargo trains and haulers, heavy machinery",
    "sorrow:lament": "melancholy and loss: ruins of a once great place, a lone mourning figure, quiet sadness",
    "ancient:temple": "ancient and mystical: temples, relics, monoliths, alien shrines, sacred mystery",
}


def _render(path, seconds, seed, mood, variant, lead_kind=None, contour=None, sounds=()):
    """Build one cue; it gets a new melody on top unless it is a soundscape, the machines or a cue
    that already carries its own tune (horn, theremin, music box)."""
    name, fn, scales, bars, low, high, ambient = variant
    c = Cue(seconds, seed, scales, bars, low, high)
    c.mood = mood
    c.sounds = list(sounds)
    fn(c)
    tune = f", sounds: {', '.join(sounds)}" if name == "soundscape" and sounds else ""
    if name not in ("soundscape", "machines", "brass", "vibes", "music box") and lead_kind != "none":
        line, kind = melody(c, seed, lead_kind, contour)
        c.add(line, 0.28, float(c.rng.uniform(0.4, 0.65)))
        tune += f", {kind} melody"
    c.write(path, *((0.4, 0.6) if ambient else (0.02, 0.2)))
    return f"{c.mode} on {c.root}{tune}"


def cue(path, seconds, seed, mood, avoid=(), prefer=()):
    """Write a cue for a mood; returns (variant id, description).

    prefer: cue ids Claude chose for this picture, best first (FITS), plus "lead:<instrument or none>"
    and "contour:<shape>" for the melody and "sound:<name>" for a soundscape (SOUNDS). When a fitting
    soundscape is among them and none ran in the last four posts, it plays half the time. Otherwise:
    the best one, unless it was among the last cues (avoid), then the next; the mood follows it.
    avoid: recently used variant ids, oldest first. Without prefer, a variant not among them is
    picked at random; when all were used, the one used longest ago, so the variants take turns.
    """
    rng = np.random.default_rng(seed)
    avoid = list(avoid)
    lead_kind = next((p.split(":", 1)[1] for p in prefer if p.startswith("lead:")), None)
    contour = next((p.split(":", 1)[1] for p in prefer if p.startswith("contour:")), None)
    sounds = [p.split(":", 1)[1] for p in prefer if p.startswith("sound:")]
    chosen = [p for p in prefer if p in FITS]
    if chosen:
        best = next((p for p in chosen if p not in avoid[-2:]), chosen[0])
        scape = next((p for p in chosen if p.endswith(":soundscape")), None)
        if scape and sounds and not any(a.endswith(":soundscape") for a in avoid[-4:]) and rng.random() < 0.5:
            best = scape  # now and then the pure sound of the place, when Claude found one that fits
        mood, wanted = best.split(":")
        variant = next(v for v in RECIPES[mood] if v[0].replace(" ", "_") == wanted)
        return f"{mood}:{wanted}", f"{mood} cue '{variant[0]}' (chosen for the picture), " + \
            _render(path, seconds, seed, mood, variant, lead_kind, contour, sounds)

    def last_use(v):
        vid = f"{mood}:{v[0]}".replace(" ", "_")
        return max((i for i, a in enumerate(avoid) if a == vid), default=-1)

    unused = [v for v in RECIPES[mood] if last_use(v) < 0]
    variant = unused[int(rng.integers(len(unused)))] if unused else min(RECIPES[mood], key=last_use)
    return f"{mood}:{variant[0]}", f"{mood} cue '{variant[0]}', " + _render(path, seconds, seed, mood, variant)
