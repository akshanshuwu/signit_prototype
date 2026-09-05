"""Ingest engine — Phase 2.

Reads .iq / .wav / .bin captures into a common complex64 representation
with fs/fc metadata and a streaming SHA-256 chain-of-custody hash.

Large-file strategy (user locked choice):
- Raw I/Q (.iq/.bin): counted + hashed in chunks, accessed via
  numpy.memmap (never fully loaded). A bounded preview (first PREVIEW_N
  samples) is materialized for estimators/plots.
- .wav: decoded via scipy.io.wavfile (libsndfile optional later);
  stereo -> I=left/Q=right, mono -> I with Q=0. File's own fs wins.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field

import numpy as np

SUPPORTED_EXTS = (".iq", ".wav", ".bin")

# dtype selector labels (must match FilePanel combo entries)
DTYPE_COMPLEX64 = "complex64 (I/Q interleaved float32)"
DTYPE_INT16 = "int16 (I/Q interleaved)"
DTYPE_COMPLEX128 = "complex128"
DTYPE_LABELS = (DTYPE_COMPLEX64, DTYPE_INT16, DTYPE_COMPLEX128)

HASH_CHUNK = 4 * 1024 * 1024
PREVIEW_N = 262_144  # 256k samples materialized for plots/estimators


@dataclass
class IngestResult:
    path: str
    kind: str  # "iq" | "wav"
    n_samples: int
    fs: int
    fc: float
    dtype_label: str
    sha256: str
    preview: np.ndarray = field(repr=False)  # complex64, len <= PREVIEW_N
    memmap_path: str | None = None  # raw path backing memmap views (iq only)
    file_fs: int | None = None  # wav: fs read from file header
    note: str = ""

    @property
    def duration_s(self) -> float:
        return self.n_samples / self.fs if self.fs else 0.0


class IngestError(ValueError):
    pass


def sha256_stream(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(HASH_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _raw_count(path: str, dtype_label: str) -> tuple[int, np.dtype]:
    size = os.path.getsize(path)
    if dtype_label == DTYPE_INT16:
        itemsize = 2  # int16; I/Q pairs
        if size % 4 != 0:
            raise IngestError(f"{os.path.basename(path)}: size {size} not a multiple of 4 bytes for int16 I/Q pairs")
        return size // 4, np.dtype(np.int16)
    if dtype_label == DTYPE_COMPLEX128:
        itemsize = 16
        if size % itemsize != 0:
            raise IngestError(f"{os.path.basename(path)}: size {size} not a multiple of 16 bytes for complex128")
        return size // itemsize, np.dtype(np.complex128)
    # complex64 default
    itemsize = 8
    if size % itemsize != 0:
        raise IngestError(f"{os.path.basename(path)}: size {size} not a multiple of 8 bytes for complex64 I/Q")
    return size // itemsize, np.dtype(np.complex64)


def _raw_preview(path: str, dtype_label: str, n: int) -> np.ndarray:
    """Materialize first n complex64 samples of a raw file without full load."""
    count, raw_dtype = _raw_count(path, dtype_label)
    take = min(n, count)
    if take == 0:
        return np.zeros(0, dtype=np.complex64)
    if dtype_label == DTYPE_INT16:
        mm = np.memmap(path, dtype=np.int16, mode="r", shape=(take * 2,))
        out = (mm.astype(np.float32) / 32768.0)[0::2] + 1j * (mm.astype(np.float32) / 32768.0)[1::2]
        return np.ascontiguousarray(out, dtype=np.complex64)
    mm = np.memmap(path, dtype=raw_dtype, mode="r", shape=(take,))
    return np.ascontiguousarray(mm.astype(np.complex64))


def raw_view(path: str, dtype_label: str) -> np.memmap:
    """Full memmap view of a raw file as complex64 (lazy, for engine consumers)."""
    count, raw_dtype = _raw_count(path, dtype_label)
    if dtype_label == DTYPE_INT16:
        mm = np.memmap(path, dtype=np.int16, mode="r", shape=(count * 2,))
        f = (mm.astype(np.float32) / 32768.0)
        return (f[0::2] + 1j * f[1::2]).astype(np.complex64)
    mm = np.memmap(path, dtype=raw_dtype, mode="r", shape=(count,))
    if raw_dtype == np.dtype(np.complex64):
        return mm
    return mm.astype(np.complex64)


def _read_wav(path: str) -> tuple[np.ndarray, int]:
    try:
        from scipy.io import wavfile
    except ImportError as exc:
        raise IngestError("scipy is required for .wav ingest (pip install scipy)") from exc
    try:
        rate, data = wavfile.read(path)
    except Exception as exc:
        raise IngestError(f"{os.path.basename(path)}: could not decode WAV ({exc})") from exc
    arr = np.asarray(data)
    if arr.size == 0:
        raise IngestError(f"{os.path.basename(path)}: WAV contains no samples")
    # Normalize integer PCM to [-1, 1]; float wavs pass through.
    if np.issubdtype(arr.dtype, np.integer):
        scale = float(max(-np.iinfo(arr.dtype).min, np.iinfo(arr.dtype).max))
        f = arr.astype(np.float32) / scale
    else:
        f = arr.astype(np.float32)
    if f.ndim == 1:
        iq = f + 0j
    else:
        ch = f.T
        i = ch[0]
        q = ch[1] if ch.shape[0] > 1 else np.zeros_like(i)
        iq = i + 1j * q
    return np.ascontiguousarray(iq, dtype=np.complex64), int(rate)


def ingest_file(path: str, fs: int = 48000, fc: float = 0.0, dtype_label: str = DTYPE_COMPLEX64) -> IngestResult:
    """Ingest any supported capture. Never fully loads raw files into RAM."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise IngestError(f"{os.path.basename(path)} isn't supported — please use .iq, .wav or .bin files.")
    if not os.path.isfile(path):
        raise IngestError(f"{os.path.basename(path)} could not be read.")
    digest = sha256_stream(path)
    if ext == ".wav":
        iq, file_fs = _read_wav(path)
        return IngestResult(
            path=path, kind="wav", n_samples=len(iq), fs=file_fs, fc=fc,
            dtype_label="wav-pcm", sha256=digest,
            preview=iq[:PREVIEW_N].copy(), file_fs=file_fs,
            note=f"wav fs {file_fs} Hz from header",
        )
    if dtype_label not in DTYPE_LABELS:
        raise IngestError(f"unknown dtype '{dtype_label}'")
    n, _ = _raw_count(path, dtype_label)
    if n == 0:
        raise IngestError(f"{os.path.basename(path)}: file is empty")
    preview = _raw_preview(path, dtype_label, PREVIEW_N)
    return IngestResult(
        path=path, kind="iq", n_samples=n, fs=int(fs), fc=float(fc),
        dtype_label=dtype_label, sha256=digest, preview=preview,
        memmap_path=path, note=f"memmap {dtype_label}",
    )


def log_lines(result: IngestResult) -> list[str]:
    short = result.sha256[:16]
    return [
        f"ingest ok: {result.n_samples} samples @ {result.fs} Hz ({result.duration_s:.2f} s)",
        f"sha256: {short}… ({os.path.basename(result.path)})",
        f"dtype: {result.dtype_label} | fc {result.fc:g} Hz | {result.note}",
    ]
