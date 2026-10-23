"""Synthesized sci-fi soundtracks as stereo WAV files.

synth_audio:    the original quiet drone + wind (used by make_reel.py).
soundtrack:     a different mix for every seed - two to four layers out of
                pad chords, arpeggios, theremin, radio pings, a heartbeat
                pulse, drone and space wind, in a random key, scale, tempo
                and stereo placement.
"""

import wave

import numpy as np

SR = 48000
SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "whole tone": [0, 2, 4, 6, 8, 10],
    "major": [0, 2, 4, 5, 7, 9, 11],
}


def write_wav(path, sig, sr=SR):
    sig = sig / (np.abs(sig).max() + 1e-9) * 0.7
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((sig * 32767).astype("<i2").tobytes())


def synth_audio(path, seconds, base_hz, cuts, seed, sr=SR):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * sr)) / sr
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t)
    chans = []
    for detune in (0.997, 1.003):
        f = base_hz * detune
        tone = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)
                + 0.3 * np.sin(2 * np.pi * f * 2.01 * t) + 0.15 * np.sin(2 * np.pi * f * 4.02 * t))
        noise = rng.normal(0, 1, t.size)
        wind = np.zeros_like(noise)
        a = 0.02
        acc = 0.0
        for k in range(0, t.size, 64):  # cheap block-wise one-pole low-pass
            acc = acc + a * (noise[k:k + 64].mean() * 8 - acc)
            wind[k:k + 64] = acc
        whoosh = np.zeros_like(t)
        for c in cuts:
            whoosh += np.exp(-((t - c) / 0.35) ** 2)
        chans.append(tone * lfo * 0.5 + wind * 0.6 + noise * whoosh * 0.08)
    sig = np.stack(chans, axis=1)
    env = np.minimum(1, np.minimum(t / 1.0, (seconds - t) / 1.0))[:, None]
    write_wav(path, sig * env, sr)


# ------------------------------------------------------------ soundtrack layers

def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def lowpass_noise(rng, n, cutoff, sr=SR):
    spec = np.fft.rfft(rng.normal(0, 1, n))
    f = np.fft.rfftfreq(n, 1 / sr)
    spec /= 1 + (f / cutoff) ** 4
    out = np.fft.irfft(spec, n)
    return out / (np.abs(out).max() + 1e-9)


def echo(x, delay_s, feedback, repeats=4, sr=SR):
    out = x.copy()
    d = int(delay_s * sr)
    for k in range(1, repeats + 1):
        if k * d >= len(x):
            break
        out[k * d:] += x[:-k * d] * feedback ** k
    return out


def tone(f, t, bright):
    """A few harmonics; bright adds the upper ones (saw-like)."""
    sig = np.sin(2 * np.pi * f * t)
    for h in range(2, 6 if bright else 3):
        sig += np.sin(2 * np.pi * f * h * t) / h ** 1.3
    return sig


def pad(rng, t, notes):
    chord = [notes[i] for i in sorted(rng.choice(len(notes), size=min(4, len(notes)), replace=False))]
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * rng.uniform(0.05, 0.2) * t + rng.uniform(0, 6))
    sig = sum(tone(hz(n) * rng.uniform(0.997, 1.003), t, rng.random() < 0.5) for n in chord)
    return sig * swell


def arpeggio(rng, t, notes):
    step = 60 / rng.uniform(90, 150) / rng.choice([2, 4])
    pattern = rng.choice(notes[:6], size=rng.choice([3, 4, 6, 8]))
    sig = np.zeros_like(t)
    decay = rng.uniform(6, 18)
    for i, start in enumerate(np.arange(0, t[-1], step)):
        k = (t >= start) & (t < start + step * 3)
        tt = t[k] - start
        sig[k] += tone(hz(pattern[i % len(pattern)] + 12), tt, True) * np.exp(-decay * tt)
    return echo(sig, step * rng.choice([1.5, 3]), 0.45)


def theremin(rng, t, notes):
    seq = rng.choice(notes, size=rng.integers(3, 6)) + 12
    pos = np.minimum((t / t[-1] * len(seq)).astype(int), len(seq) - 1)
    f = np.convolve(hz(seq)[pos], np.ones(SR // 4) / (SR // 4), mode="same")  # glide
    f *= 1 + 0.012 * np.sin(2 * np.pi * rng.uniform(5, 7) * t)  # vibrato
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) + 0.2 * np.sin(2 * phase)


def pings(rng, t, notes):
    sig = np.zeros_like(t)
    for start in np.sort(rng.uniform(0.5, t[-1] - 1, size=rng.integers(3, 8))):
        k = t >= start
        tt = t[k] - start
        sig[k] += np.sin(2 * np.pi * hz(rng.choice(notes) + 24) * tt) * np.exp(-9 * tt)
    return echo(sig, rng.uniform(0.25, 0.5), 0.5, repeats=6)


def pulse(rng, t, notes):
    beat = 60 / rng.uniform(50, 80)
    sig = np.zeros_like(t)
    for start in np.arange(0.2, t[-1], beat):
        for off, amp in ((0, 1.0), (0.18, 0.6)):
            k = t >= start + off
            tt = t[k] - start - off
            sig[k] += amp * np.sin(2 * np.pi * 50 * tt * np.exp(-3 * tt)) * np.exp(-12 * tt)
    return sig


def drone(rng, t, notes):
    f = hz(notes[0] - 12)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t)) * (
        0.7 + 0.3 * np.sin(2 * np.pi * rng.uniform(0.05, 0.15) * t))


def wind(rng, t, notes):
    sweep = 0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.04, 0.12) * t + rng.uniform(0, 6))
    return lowpass_noise(rng, len(t), rng.uniform(300, 1200)) * sweep


LAYERS = {"pad": (pad, 0.5), "arpeggio": (arpeggio, 0.35), "theremin": (theremin, 0.3),
          "pings": (pings, 0.35), "pulse": (pulse, 0.6), "drone": (drone, 0.45), "wind": (wind, 0.35)}


def soundtrack(path, seconds, seed):
    """Write a random sci-fi soundtrack; returns a short description of the mix."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    scale = rng.choice(list(SCALES))
    root = int(rng.integers(45, 57))  # A2 .. G#3
    notes = [root + s for s in SCALES[scale]] + [root + 12 + s for s in SCALES[scale]]
    names = list(rng.choice(["pad", "arpeggio", "theremin", "pings", "pulse"],
                            size=int(rng.integers(1, 4)), replace=False))
    names += list(rng.choice(["drone", "wind"], size=int(rng.integers(1, 3)), replace=False))
    left = np.zeros_like(t)
    right = np.zeros_like(t)
    for name in names:
        fn, gain = LAYERS[name]
        layer = fn(rng, t, notes)
        layer = layer / (np.abs(layer).max() + 1e-9) * gain
        pan = rng.uniform(0.2, 0.8)
        left += layer * (1 - pan)
        right += layer * pan
    env = np.minimum(1, np.minimum(t / 0.8, (seconds - t) / 1.0))
    write_wav(path, np.stack([left, right], axis=1) * env[:, None])
    return f"{scale} on {root}: {', '.join(names)}"
