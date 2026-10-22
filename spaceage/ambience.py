"""Quiet synthesized space ambience (drone + wind) as a stereo WAV."""

import wave

import numpy as np


def synth_audio(path, seconds, base_hz, cuts, seed, sr=48000):
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
    sig *= env
    sig = sig / (np.abs(sig).max() + 1e-9) * 0.7
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((sig * 32767).astype("<i2").tobytes())
