"""Synthesized sci-fi soundtracks as stereo WAV files.

synth_audio:    the original quiet drone + wind (used by make_reel.py).
soundtrack:     a different mix for every seed - always one sustained bed
                (pad, string or brass ensemble), at most one sparse accent
                (slow theremin, radio pings, heartbeat pulse, ring mod clangs)
                and drone or space wind, in a random key, scale and stereo
                placement. Fast patterns (arpeggios, sequences, bleeps) stay out
                of the default mix: in an 8 second reel they sound like tinkling. Some layers imitate classic analog
                synthesizers: a 1970s modular (resonant filter sequences,
                sample & hold bleeps, ring modulation) and a 1970s/80s
                polyphonic (detuned brass and string pads with swelling
                vibrato and ribbon pitch bends).
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
    seq = rng.choice(notes, size=rng.integers(2, 4)) + 12
    pos = np.minimum((t / t[-1] * len(seq)).astype(int), len(seq) - 1)
    f = np.convolve(hz(seq)[pos], np.ones(SR // 4) / (SR // 4), mode="same")  # glide
    f *= 1 + 0.012 * np.sin(2 * np.pi * rng.uniform(5, 7) * t)  # vibrato
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) + 0.2 * np.sin(2 * phase)


def pings(rng, t, notes):
    sig = np.zeros_like(t)
    for start in np.sort(rng.uniform(0.5, t[-1] - 1, size=rng.integers(2, 4))):
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


# ------------------------------------------------- analog synthesizer layers

def saw(f, t, top=6000):
    """Band-limited sawtooth (additive), f may be an array (glides)."""
    f0 = float(np.max(f))
    phase = 2 * np.pi * np.cumsum(np.broadcast_to(f, t.shape)) / SR
    return sum(np.sin(h * phase) / h for h in range(1, max(2, int(top / f0)) + 1))


def resonant_lowpass(x, cutoff, q):
    """State-variable filter; cutoff (Hz) may change per sample. q 0.5 (soft) .. 10 (screaming)."""
    cutoff = np.broadcast_to(np.clip(cutoff, 20, SR / 6), x.shape)
    fc = (2 * np.sin(np.pi * cutoff / SR)).tolist()
    damp = 1 / q
    low = band = 0.0
    out = [0.0] * len(x)
    for i, (v, f) in enumerate(zip(x.tolist(), fc)):
        low += f * band
        band += f * (v - low - damp * band)
        out[i] = low
    return np.array(out)


def modular_sequence(rng, t, notes):
    """1970s modular: sequenced saw/pulse through a sweeping resonant filter."""
    step = 60 / rng.uniform(100, 160) / 2
    pattern = rng.choice(notes[:8], size=rng.choice([4, 5, 8]))
    pos = (t / step).astype(int)
    f = hz(np.array(pattern)[pos % len(pattern)])
    osc = saw(f, t) if rng.random() < 0.6 else np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    gate = np.exp(-rng.uniform(4, 10) * (t % step))
    sweep = 400 + 2600 * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.08, 0.25) * t))
    return echo(resonant_lowpass(osc * gate, sweep * (0.4 + gate), rng.uniform(4, 9)), step * 3, 0.35)


def sample_hold(rng, t, notes):
    """Random-pitch bleeps from a sample & hold clock (classic computer noises)."""
    step = 1 / rng.uniform(6, 14)
    steps = int(t[-1] / step) + 1
    pitches = rng.uniform(300, 2400, size=steps)
    f = pitches[(t / step).astype(int)]
    blip = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-25 * (t % step))
    return resonant_lowpass(blip, f * 1.2, 6) * (rng.random(steps)[(t / step).astype(int)] < 0.7)


def ring_mod(rng, t, notes):
    """Ring modulation: two tones multiplied give metallic, bell-like clangs."""
    a = np.sin(2 * np.pi * hz(rng.choice(notes) + 12) * t)
    b = np.sin(2 * np.pi * rng.uniform(80, 700) * t * (1 + 0.02 * np.sin(2 * np.pi * 0.3 * t)))
    hits = np.zeros_like(t)
    for start in np.arange(rng.uniform(0, 1), t[-1], rng.uniform(1.2, 2.5)):
        k = t >= start
        hits[k] += np.exp(-2.5 * (t[k] - start))
    return echo(a * b * hits, rng.uniform(0.3, 0.6), 0.4)


def poly_brass(rng, t, notes):
    """1970s/80s polyphonic brass: detuned saw pairs, slow filter opening, swelling vibrato, ribbon bend."""
    chord = [notes[i] for i in sorted(rng.choice(len(notes), size=3, replace=False))]
    vib = 1 + 0.006 * np.minimum(1, t / 3) * np.sin(2 * np.pi * 5.5 * t)
    bend_at = rng.uniform(4, 6.5)
    bend = 2 ** (np.clip((t - bend_at) / 1.2, 0, 1) * rng.choice([-2, -1, 2]) / 12)  # ribbon slide
    sig = sum(saw(hz(n) * d * vib * bend, t, 4000) for n in chord for d in (0.996, 1.004))
    cutoff = 300 + 2500 * (1 - np.exp(-t / rng.uniform(0.8, 2.0)))
    return resonant_lowpass(sig, cutoff, 1.2)


def poly_strings(rng, t, notes):
    """Wide string ensemble: many slightly detuned, slowly drifting saws, soft attack."""
    chord = [notes[i] for i in sorted(rng.choice(len(notes), size=4, replace=False))]
    sig = np.zeros_like(t)
    for n in chord:
        for _ in range(3):
            drift = 1 + 0.004 * np.sin(2 * np.pi * rng.uniform(0.2, 0.8) * t + rng.uniform(0, 6))
            sig += saw(hz(n) * drift, t, 3000)
    attack = 1 - np.exp(-t / rng.uniform(0.6, 1.5))
    return resonant_lowpass(sig * attack, 1800, 0.8)


LAYERS = {"pad": (pad, 0.5), "arpeggio": (arpeggio, 0.35), "theremin": (theremin, 0.3),
          "pings": (pings, 0.35), "pulse": (pulse, 0.6), "drone": (drone, 0.45), "wind": (wind, 0.35),
          "modular sequence": (modular_sequence, 0.4), "sample & hold": (sample_hold, 0.3),
          "ring mod": (ring_mod, 0.3), "poly brass": (poly_brass, 0.45), "poly strings": (poly_strings, 0.45)}
BEDS = ["pad", "poly brass", "poly strings"]
ACCENTS = ["theremin", "pings", "pulse", "ring mod"]


def soundtrack(path, seconds, seed, scales=None, low=False):
    """Write a random sci-fi soundtrack; returns a short description of the mix.
    scales: allowed scale names (from mood.py), low: keep it deep."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    scale = rng.choice([s for s in (scales or SCALES) if s in SCALES] or list(SCALES))
    root = int(rng.integers(40, 48) if low else rng.integers(45, 57))  # E2 .. D#3 or A2 .. G#3
    notes = [root + s for s in SCALES[scale]] + [root + 12 + s for s in SCALES[scale]]
    names = [str(rng.choice(BEDS))]
    if rng.random() < 0.6:
        names.append(str(rng.choice(ACCENTS)))
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
