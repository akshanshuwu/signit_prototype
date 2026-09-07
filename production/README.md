# SIGNIT Production (Offline, Finals) — native Windows .exe

Locked stack: PySide6 + pyqtgraph + Qt-Material Dark + in-process Python (NumPy + pyFFTW + SciPy + Numba + memmap + QThread) + ONNX Runtime + galois + scikit-commpy + pyldpc + PyInstaller single .exe.

Status: Phases 0–6 done. Ops-console GUI ingests real `.iq/.wav/.bin` (memmap + streaming hash) and runs estimators → try-all demod → ML vote ensemble (cumulants + sklearn RandomForest + ONNX CNN) → FEC assessment (pure-NumPy RS + Viterbi + de-interleave try-all), all wired into Report/tabs/log.
Independent from prototype — no imports from `prototype/`.

## What exists
- `app/` — ops console: `main.py` entry (`--smoke` headless check), `mainwindow.py`, widgets (`file_panel`, `results_tabs`, `plots`, `report_card`, `bits_view`, `comparator`, `mission_log`), `demo_store` (4 bundled captures)
- `engine/` — `ingest.py` (memmap chunked + sha256), `estimators.py` (Welch PSD, spectrogram, constellation, SNR/BW), `demod.py` (BPSK/QPSK/16QAM/2FSK try-all + EVM rank + sync finder), `fec.py` (RS codec + Viterbi + de-interleave try-all; galois/commpy/pyldpc are optional accelerators)
- `ml/` — `cumulants.py`, `ensemble.py` (demod 0.40 / cumulants 0.25 / sklearn 0.20 / cnn 0.15 + lone-CNN-abstain guard), `cnn_onnx.py` (carrier+timing-corrected symbol images), `synth.py`, `train_cnn.py`
- `ml/models/signit_cnn.onnx` — trained artifact (repo-excluded; reproduce via training below)
- `tests/` — 66 tests across test_phase1–6 + test_smoke, all green offscreen
- `signit.spec` — PyInstaller single-file spec (hidden imports + demo-data bundling; proven only on Windows)
- `requirements.txt` — pinned deps for Python 3.10 (CI + .exe target)

## Run (dev, macOS/Linux — Python 3.10 venv)
```
cd production
uv python install 3.10 && uv venv --python 3.10 .venv
.venv/bin/python -m ensurepip && .venv/bin/python -m pip install --upgrade pip
# Staged install: pyldpc needs numpy present at build time (pip build isolation hides it)
.venv/bin/python -m pip install "numpy==1.26.4" "scipy==1.13.1" "scikit-learn==1.5.1"
.venv/bin/python -m pip install --no-build-isolation "pyldpc==0.7.7"
.venv/bin/python -m pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q
QT_QPA_PLATFORM=offscreen .venv/bin/python -m app.main --smoke
```

## Train the CNN (isolated env — torch must NOT enter the runtime venv)
```
uv venv --python 3.10 .train-venv && .train-venv/bin/python -m ensurepip
.train-venv/bin/python -m pip install torch onnx numpy
.train-venv/bin/python -m ml.train_cnn   # writes ml/models/signit_cnn.onnx (gitignored)
```

## Build .exe (Windows, via GitHub Actions)
Push changes under `production/` — workflow `windows-build` installs requirements on Python 3.10, runs the smoke test, builds and uploads `dist/SIGNIT.exe` as artifact `SIGNIT-windows-exe`. Train the model before release builds so the CNN vote is live in the .exe.
