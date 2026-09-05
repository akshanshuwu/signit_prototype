"""Phase 6 tests — GF(256), RS codec, Viterbi, de-interleavers, try-all assessment."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.fec import (
    RSCodec,
    RSDecodeError,
    assess_bits,
    backend_status,
    block_deinterleave,
    block_interleave,
    conv_deinterleave,
    conv_encode,
    conv_interleave,
    diag_deinterleave,
    diag_interleave,
    gf_div,
    gf_mul,
    pr_deinterleave,
    pr_interleave,
    viterbi_decode,
)


def test_gf_arithmetic():
    rng = np.random.default_rng(0)
    for _ in range(200):
        a, b = int(rng.integers(1, 256)), int(rng.integers(1, 256))
        assert gf_div(gf_mul(a, b), b) == a
        assert gf_div(gf_mul(a, b), a) == b
    assert gf_mul(0, 123) == 0 and gf_mul(200, 0) == 0
    with pytest.raises(ZeroDivisionError):
        gf_div(5, 0)


def test_rs_roundtrip_at_capacity():
    rng = np.random.default_rng(1)
    for (n, k, t) in [(15, 11, 2), (31, 23, 4), (31, 15, 8), (63, 47, 8), (255, 223, 16)]:
        codec = RSCodec(n, k)
        msg = rng.integers(0, 256, k).astype(np.uint8).tobytes()
        cw = bytearray(codec.encode(msg))
        for e in rng.choice(n, t, replace=False):
            cw[e] ^= 0xFF
        out, nerr = codec.decode(bytes(cw))
        assert out == msg, f"RS({n},{k})"
        assert nerr == t


def test_rs_beyond_capacity_fails():
    rng = np.random.default_rng(2)
    codec = RSCodec(31, 15)
    msg = rng.integers(0, 256, 15).astype(np.uint8).tobytes()
    cw = bytearray(codec.encode(msg))
    for e in rng.choice(31, 9, replace=False):  # t+1 = 9 > 8
        cw[e] ^= 0xFF
    with pytest.raises(RSDecodeError):
        codec.decode(bytes(cw))


def test_rs_shortened():
    rng = np.random.default_rng(3)
    codec = RSCodec(31, 23)
    msg = rng.integers(0, 256, 10).astype(np.uint8).tobytes()  # shorter than k
    cw = bytearray(codec.encode(msg))
    for e in rng.choice(31, 4, replace=False):
        cw[e] ^= 0x5A
    out, _nerr = codec.decode(bytes(cw))
    assert out[-10:] == msg  # front-pad occupies the head


def test_rs_bad_params():
    with pytest.raises(ValueError):
        RSCodec(300, 200)
    with pytest.raises(ValueError):
        RSCodec(15, 15)


def test_viterbi_roundtrip():
    rng = np.random.default_rng(4)
    for K in (3, 5, 7):
        bits = rng.integers(0, 2, 300).astype(np.uint8)
        coded = conv_encode(bits, K)
        noisy = coded.copy()
        flip = rng.random(len(coded)) < 0.05
        noisy[flip] ^= 1
        dec, metric = viterbi_decode(noisy, K)
        assert float(np.mean(dec[: len(bits)] != bits)) < 0.01, f"K={K}"
        assert metric < 0.10


def test_viterbi_clean_metric_zero():
    rng = np.random.default_rng(5)
    bits = rng.integers(0, 2, 200).astype(np.uint8)
    _dec, metric = viterbi_decode(conv_encode(bits, 3), 3)
    assert metric == 0.0


def test_deinterleave_roundtrips():
    rng = np.random.default_rng(6)
    b = rng.integers(0, 2, 2048).astype(np.uint8)
    assert np.array_equal(block_deinterleave(block_interleave(b, 16), 16), b)
    assert np.array_equal(conv_deinterleave(conv_interleave(b, 8, 4), 8, 4), b)
    assert np.array_equal(diag_deinterleave(diag_interleave(b, 16), 16), b)
    assert np.array_equal(pr_deinterleave(pr_interleave(b, 7), 7), b)


def test_assess_recovers_rs_block():
    rng = np.random.default_rng(7)
    codec = RSCodec(31, 15)
    msg = rng.integers(0, 256, 60).astype(np.uint8).tobytes()
    stream = b"".join(codec.encode(msg[i:i + 15]) for i in range(0, 60, 15))
    bits = np.unpackbits(np.frombuffer(stream, dtype=np.uint8))
    f = assess_bits(block_interleave(bits, 16))
    assert f.status == "CLEAN", f.ranking
    assert f.scheme == "RS(31,15)" and f.deint == "block-16"
    assert f.decoded[:60] == msg


def test_assess_recovers_conv_pr():
    rng = np.random.default_rng(8)
    info = rng.integers(0, 2, 400).astype(np.uint8)
    coded = conv_encode(info, 3)
    f = assess_bits(pr_interleave(coded, 7))
    assert f.status in ("CLEAN", "STRUCTURE"), f.ranking
    assert "pr-7" in f.ranking[0] or f.deint == "pr-7"


def test_assess_random_is_none():
    rng = np.random.default_rng(9)
    f = assess_bits(rng.integers(0, 2, 2000).astype(np.uint8))
    assert f.status == "NONE"


def test_assess_short_abstains():
    f = assess_bits(np.ones(32, dtype=np.uint8))
    assert f.status == "NONE" and "abstains" in f.note


def test_backend_status_keys():
    st = backend_status()
    assert st["builtin_rs"] is True and st["builtin_viterbi"] is True
    assert all(k in st for k in ("galois", "commpy", "pyldpc"))


def test_demo_dict_fec_override(tmp_path):
    from app.demo_store import validate_demo
    from engine.demod import demodulate_preview
    from engine.estimators import analyze_preview, to_demo_dict
    from engine.fec import RSCodec, assess_bits, block_interleave
    from engine.ingest import ingest_file
    from ml.ensemble import run_ml_vote

    rng = np.random.default_rng(10)
    FS = 48000
    codec = RSCodec(31, 15)
    msg = rng.integers(0, 256, 30).astype(np.uint8).tobytes()
    stream = b"".join(codec.encode(msg[i:i + 15]) for i in range(0, 30, 15))
    bits = np.unpackbits(np.frombuffer(stream, dtype=np.uint8))
    tx = block_interleave(bits, 16)
    # BPSK modulate the interleaved codeword stream (rectangular, 2000 sym/s).
    sym = np.where(tx, 1.0, -1.0).astype(np.complex64)
    x = np.repeat(sym, FS // 2000)
    t = np.arange(len(x)) / FS
    rng2 = np.random.default_rng(11)
    x = ((x + (rng2.standard_normal(len(x)) + 1j * rng2.standard_normal(len(x))) * 0.02)
         * np.exp(2j * np.pi * 150 * t)).astype(np.complex64)
    p = tmp_path / "rs.iq"
    x.tofile(p)
    ing = ingest_file(str(p), fs=FS)
    est = analyze_preview(ing.preview, ing.fs, ing.fc)
    demod = demodulate_preview(ing.preview, ing.fs)
    assert demod.modulation == "BPSK", demod.candidates
    _cum, v, _cnn, _lines = run_ml_vote(ing.preview, ing.fs, demod)
    fec = assess_bits(demod.bits)
    demo = to_demo_dict(est, ing, demod=demod, vote=v, fec=fec)
    assert validate_demo(demo) == []
    if fec.status == "CLEAN":
        assert demo["bits_preview"]["hex"] == fec.hex_text
        assert "FEC" in demo["comparator"]["note"]


def test_mainwindow_ingest_shows_fec(tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from app.mainwindow import MainWindow
    from engine.ingest import ingest_file as _ingest
    from ml.synth import FS, synth

    _app = QApplication.instance() or QApplication([])
    x = synth("BPSK", 20.0, 46)
    p = tmp_path / "bpsk.iq"
    x.tofile(p)
    win = MainWindow()
    try:
        win._on_ingested(_ingest(str(p), fs=FS))
        text = win.mission_log.toPlainText()
        assert "fec:" in text
        assert win.error_banner.isHidden()
    finally:
        win.close()
