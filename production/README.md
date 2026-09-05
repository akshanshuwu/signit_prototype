# SIGNIT Production (Offline, Finals) — native Windows .exe

Locked stack: PySide6 + pyqtgraph + Qt-Material Dark + in-process Python (NumPy + pyFFTW + SciPy + Numba + memmap + QThread) + ONNX Runtime + galois + scikit-commpy + pyldpc + PyInstaller single .exe.

Status: Phase 4 done (real demod — BPSK/QPSK/16QAM/2FSK try-all + EVM rank, sync-word finder, header/payload split; ML classifier still pending).
Independent from prototype — no imports from `prototype/`.

## Phase 0 — what exists
- `app/main.py` — entry point (`python3 -m app.main` from `production/`)
- `app/mainwindow.py` — minimal shell (full ops-console layout lands in Phase 1)
- `engine/`, `ml/` — empty packages (real code lands in Phases 2–5)
- `tests/test_smoke.py` — import + window contract tests
- `signit.spec` — PyInstaller single-file spec (hardened in Phase 8)
- `requirements.txt` — pinned deps (CI installs with Python 3.10)

## Run (dev, macOS/Linux)
```
cd production
python3 -m pip install PySide6 pyqtgraph qt-material pytest
QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke
python3 -m pytest tests/test_smoke.py -v
```

## Build .exe (Windows, via GitHub Actions)
Push changes under `production/` — workflow `windows-build` builds and
uploads `dist/SIGNIT.exe` as artifact `SIGNIT-windows-exe`.
