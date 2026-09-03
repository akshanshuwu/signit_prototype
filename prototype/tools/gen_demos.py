"""Local-only demo JSON generator (NOT deployed). Run once per sample set.

Usage:
  python3 tools/gen_demos.py --only qpsk
  python3 tools/gen_demos.py --all

Output: prototype/frontend/public/demo/{bpsk,qpsk,qam16,fsk2}.json
Spec: IMPLEMENTATION_PLAN.md section 2+3. Frontend-only v1.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy import signal as spsig
from scipy.ndimage import zoom as ndzoom

FS = 48000
SYM_RATE = 2000
SPS = FS // SYM_RATE  # 24
SNR_DB = 15
CONF = {"bpsk": 0.91, "qpsk": 0.94, "qam16": 0.89, "fsk2": 0.92}
LABEL = {"bpsk": "BPSK", "qpsk": "QPSK", "qam16": "16QAM", "fsk2": "2FSK"}


def add_awgn(x: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    p = float(np.mean(np.abs(x) ** 2)) + 1e-12
    snr = 10 ** (snr_db / 10)
    sigma = np.sqrt(p / snr / 2)
    return x + (rng.normal(0, sigma, x.shape) + 1j * rng.normal(0, sigma, x.shape))


def rect_pulse(symbols: np.ndarray, sps: int) -> np.ndarray:
    return np.repeat(symbols, sps)


def gen_symbols(mod: str, n_sym: int, rng: np.random.Generator) -> np.ndarray:
    if mod == "bpsk":
        bits = rng.integers(0, 2, n_sym)
        return (2 * bits - 1).astype(np.complex128)
    if mod == "qpsk":
        bits = rng.integers(0, 2, 2 * n_sym)
        i = 2 * bits[0::2] - 1
        q = 2 * bits[1::2] - 1
        return (i + 1j * q) / np.sqrt(2)
    if mod == "qam16":
        vals = np.array([-3, -1, 1, 3])
        i = vals[rng.integers(0, 4, n_sym)]
        q = vals[rng.integers(0, 4, n_sym)]
        return (i + 1j * q) / np.sqrt(10)
    raise ValueError(mod)


def gen_fsk(n_bits: int, dev: float, fs: int, rng: np.random.Generator) -> np.ndarray:
    bits = rng.integers(0, 2, n_bits)
    # +1 -> +dev/2, 0 -> -dev/2, continuous phase, 24 samples per bit at 2k bit/s
    sps = fs // 2000
    freq = np.where(np.repeat(bits, sps) == 1, dev / 2, -dev / 2)
    phase = 2 * np.pi * np.cumsum(freq) / fs
    return np.exp(1j * phase)


def psd_512(x: np.ndarray, fs: int):
    f, pxx = spsig.welch(x, fs=fs, nperseg=1024, return_onesided=False)
    f = np.fft.fftshift(f)
    pxx = np.fft.fftshift(pxx)
    # interp to exactly 512 pts, centered
    xi = np.linspace(0, len(f) - 1, 512)
    fi = np.interp(xi, np.arange(len(f)), f)
    pi = np.interp(xi, np.arange(len(pxx)), pxx)
    mag = 10 * np.log10(pi + 1e-12)
    return np.round(fi, 2).tolist(), np.round(mag, 2).tolist()


def spectro_128x64(x: np.ndarray, fs: int):
    f, t, sxx = spsig.spectrogram(x, fs=fs, nperseg=256, noverlap=192, return_onesided=False, mode="magnitude")
    f = np.fft.fftshift(f)
    sxx = np.fft.fftshift(sxx, axes=0)
    z = 20 * np.log10(sxx + 1e-9)
    # resize freq axis -> 128, time axis -> 64
    zf = ndzoom(z, (128 / z.shape[0], 64 / z.shape[1]), order=1)
    zf = zf[:128, :64]
    ti = np.linspace(float(t[0]), float(t[-1]), 64)
    fi = np.linspace(float(f[0]), float(f[-1]), 128)
    return [round(float(v), 3) for v in ti], [round(float(v), 1) for v in fi], np.round(zf, 2).tolist()


def bits_preview(mod: str, rng: np.random.Generator):
    nbytes = 64
    raw = rng.integers(0, 256, nbytes, dtype=np.int64)
    hx = " ".join(f"{int(b):02X}" for b in raw[:32])
    asc = "".join(chr(int(b)) if 32 <= int(b) < 127 else "." for b in raw[:32])
    lags = list(range(0, 256))
    peak_lag = 128
    vals = [round(float(0.2 + 0.72 * max(0.0, 1 - abs(l - peak_lag) / 18) + rng.normal(0, 0.02)), 3) for l in lags]
    vals[peak_lag] = round(float(max(vals[peak_lag], 0.92)), 3)
    return hx, asc, peak_lag, round(float(vals[peak_lag]), 3), lags, vals


def build(mod: str, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    if mod == "fsk2":
        n_bits = 1000
        clean = gen_fsk(n_bits, dev=2000.0, fs=FS, rng=rng)
        sym_rate = 1000
    else:
        n_sym = 2000
        clean = rect_pulse(gen_symbols(mod, n_sym, rng), SPS)
        sym_rate = SYM_RATE
    x = add_awgn(clean, SNR_DB, rng)

    freqs, mags = psd_512(x, FS)
    times, sFreqs, z = spectro_128x64(x, FS)

    # constellation: one sample per symbol/bit at center
    step = SPS
    centers = x[step // 2 :: step][:2000]
    ci = np.round(centers.real, 4).tolist()
    cq = np.round(centers.imag, 4).tolist()

    hx, asc, lag, val, lags, cvals = bits_preview(mod, rng)
    est_snr = round(float(SNR_DB + rng.normal(0, 0.4)), 1)
    wav_snr = round(float(est_snr - 5.5), 1)

    return {
        "meta": {"modulation": LABEL[mod], "fs": FS, "symbol_rate": sym_rate, "snr_db": SNR_DB, "center_freq": 0, "file": f"{mod}.iq"},
        "predictions": {
            "modulation": LABEL[mod],
            "confidence": CONF[mod],
            "votes": {"CNN": CONF[mod], "cumulants": LABEL[mod]},
            "fs_est": FS,
            "symbol_rate_est": sym_rate,
            "bw_est": 4000 if mod != "fsk2" else 3000,
            "snr_est": est_snr,
        },
        "psd": {"freqs": freqs, "mags_db": mags},
        "spectrogram": {"times": times, "freqs": sFreqs, "z_db": z},
        "constellation": {"i": ci, "q": cq},
        "bits_preview": {"hex": hx, "ascii": asc, "corr_peak": {"lag": lag, "value": val, "lags": lags, "vals": cvals}},
        "comparator": {"iq_snr": est_snr, "wav_snr": wav_snr, "note": ".wav loses phase BW, constellation collapses"},
        "log": [
            f"ingest ok: {len(x)} samples @ {FS} Hz",
            f"psd ok: 512 pts, bw ~4 kHz",
            f"spectrogram ok: 128x64",
            f"cnn={LABEL[mod]} {CONF[mod]:.2f} | cumulants={LABEL[mod]}",
            f"sync peak lag {lag} val {val}",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["bpsk", "qpsk", "qam16", "fsk2"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default="prototype/frontend/public/demo")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    mods = [args.only] if args.only else (["bpsk", "qpsk", "qam16", "fsk2"] if args.all else ["qpsk"])
    if os.path.isabs(args.out):
        outdir = args.out
    else:
        # tools/ lives in prototype/tools -> repo root SIGNIT is two levels up
        signit = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        outdir = os.path.join(signit, args.out)
    os.makedirs(outdir, exist_ok=True)

    seeds = {"bpsk": 11, "qpsk": 22, "qam16": 33, "fsk2": 44}
    for m in mods:
        d = build(m, args.seed + seeds[m])
        p = os.path.join(outdir, f"{m}.json")
        with open(p, "w") as f:
            json.dump(d, f)
        kb = os.path.getsize(p) / 1024
        print(f"wrote {p} ({kb:.0f} KB) psd={len(d['psd']['freqs'])} const={len(d['constellation']['i'])} conf={d['predictions']['confidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
