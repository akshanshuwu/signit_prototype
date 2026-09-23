# SIGNIT — Windows `.exe` Handoff Guide (READ THIS ON THE WINDOWS MACHINE)

> **Purpose:** finalize the functional offline `SIGNIT.exe` on Windows and publish it so the website (built on the Mac) can offer it as a download.
> **Split of work (locked):** Mac/Linux device = ONLY `prototype/frontend` web UI. Windows device = ONLY `production/` exe + GitHub Release. Do not mix.
> **Source of truth commit:** `d2998db0137ac12654963b8427dc2993d6826bf6` — `Prototype: real in-browser any-file DSP (up to 100MB sliced preview), remove precomputed samples, restore slate UI`. Both `akshanshuwu/signit_prototype` and `ojaswini22085/signit` `main` are at this SHA. If your checkout differs, sync first (Section 3).
> **How to use this file:** paste it as context to your local AI (opencode / any model) and follow Sections 3–7 top to bottom. Every command is copy-paste PowerShell unless marked otherwise.

---

## 1. What you are building

Single-file offline Windows desktop app: `dist/SIGNIT.exe` (console-less PySide6 GUI). File ingest is the ONLY analysis path — no sample buttons, no bundled demos, no backend, no internet required at runtime.

Pipeline per file (all in-process, no HTTP):

1. Ingest real `.iq` / `.wav` / `.bin` via memmap + streaming SHA256 (`production/engine/ingest.py`).
2. Estimators: Welch PSD + spectrogram + constellation + SNR/BW (`production/engine/estimators.py`).
3. Try-all demod BPSK/QPSK/16QAM/2FSK + EVM rank + sync-word finder + header/payload split (`production/engine/demod.py`).
4. ML vote ensemble: demod 0.40 / cumulants 0.25 / sklearn RandomForest 0.20 / CNN 0.15 + lone-CNN-abstain guard (`production/ml/ensemble.py`, `production/ml/cumulants.py`, `production/ml/cnn_onnx.py`).
5. FEC assessment: pure-NumPy RS codec + Viterbi + de-interleave try-all (Block/Convolutional/Diagonal/Pseudo-Random) with clean/structure/none verdicts (`production/engine/fec.py`). `galois` (RS) + `scikit-commpy` (Conv/Viterbi) + `pyldpc` (LDPC) are optional accelerators.
6. GUI: left file+params, center Spectrum/Waterfall/Constellation/Time tabs, right Auto-Report + confidence, bottom Mission Log, History panel (SQLite), Export Intel PDF (`production/app/`, `fpdf2`).

Reference: `TECH_STACK.md` Section 2 (Production), `production/README.md`, `production/RUN_MAC.md` (Mac parity — same code, ignore `uv`/`.venv` paths, use `py -3.10` below).

## 2. Repo map (only these matter on Windows)

```
production/
  app/main.py            # entry: flags --smoke, --history-db PATH, --no-splash (see production/app/main.py:72-121)
  app/mainwindow.py      # MainWindow shell, TAB_ORDER, _on_ingested, _demo/_source
  app/widgets/           # file_panel, results_tabs, plots, report_card, bits_view, comparator, mission_log
  app/demo_store.py      # validate_demo result-contract checker
  app/intel_pdf.py       # Export PDF (fpdf2)
  engine/ingest.py       # memmap chunked + sha256
  engine/estimators.py   # Welch PSD, spectrogram, constellation, SNR/BW
  engine/demod.py        # try-all + EVM rank + sync finder
  engine/fec.py          # RS + Viterbi + de-interleave try-all
  engine/history.py      # SQLite; default Windows %APPDATA%/SIGNIT/history.db (see production/engine/history.py:37-41)
  engine/reanalyze.py    # ROI re-analysis
  ml/cumulants.py ml/ensemble.py ml/cnn_onnx.py ml/synth.py ml/train_cnn.py ml/explain.py
  ml/models/             # GITIGNORED (.gitignore: production/ml/models/) — train locally, never commit
  tests/                 # test_phase1-7 + test_smoke + test_live_chain + test_hardening (10 files)
  requirements.txt       # pinned, Python 3.10 target (see full list in Section 4)
  signit.spec            # PyInstaller single-file spec (see production/signit.spec:1-106)
.github/workflows/windows-build.yml  # CI: windows-latest, pytest -> --smoke -> pyinstaller -> exe --smoke -> artifact SIGNIT-windows-exe
```

Key spec facts (`production/signit.spec`): `ENTRY=production/app/main.py`, `name="SIGNIT"`, single `EXE(...)`, `console=False`, `upx=True`, `excludes=["torch","torchvision","torchaudio","onnx","pytest","tkinter"]`, `datas` = `ml/models/*.onnx` WHEN PRESENT (empty list if untrained → pending-vote fallback), ~30 `hiddenimports` for Qt/plotting/DSP/ML/FEC (do not trim).

## 3. Sync repo first

```powershell
git clone https://github.com/akshanshuwu/signit_prototype.git SIGNIT
cd SIGNIT
git checkout main
git pull origin main
git rev-parse HEAD
# expect d2998db0137ac12654963b8427dc2993d6826bf6
```

If you cloned `ojaswini22085/signit` instead, that is fine — same SHA. Do NOT mix branches. Web team owns `prototype/`; do not edit it here except to read.

## 4. Prerequisites (Windows 10/11 x64)

- Python `3.10.x` from python.org, `py -3.10` on PATH (`py -3.10 --version` must print 3.10.*).
- Git. No `uv`, no `torch/onnx/torchvision`, no GNU Radio (synth-only), no display needed for smoke (`QT_QPA_PLATFORM=offscreen`).
- Pinned runtime (`production/requirements.txt`):
  `PySide6==6.7.2 pyqtgraph==0.13.7 qt-material==2.14 numpy==1.26.4 scipy==1.13.1 scikit-learn==1.5.1 onnxruntime==1.18.1 numba==0.59.1 pyFFTW==0.14.0 soundfile==0.12.1 matplotlib==3.9.2 galois==0.3.10 scikit-commpy==0.8.0 pyldpc==0.7.7 pyinstaller==6.9.0 pytest==8.3.2 PyYAML==6.0.2 fpdf2==2.8.8`
- Constraints: `numba==0.59.x` (galois 0.3.10 needs numba<0.60). `pyldpc` MUST be installed staged with `--no-build-isolation` AFTER numpy (pip build isolation hides numpy). `torch/onnx` are training-only in isolated `.train-venv`, never in runtime venv.

## 5. PRD — `.exe` (acceptance-locked)

**Users:** SIH finals judge (offline any-file test), owner (demo). No login, no network.
**Non-goals:** no web work, no `prototype/` edits, no new modulations, no SDR, no cloud.
**User stories (must all pass):**
1. Double-click `SIGNIT.exe` → splash `SIGNIT // RF SIGNAL ANALYZER` → empty READY state (Mission Log prompt, Report `UNKNOWN`). No console window.
2. Drop any `.iq/.wav/.bin` → all 6 tabs fill with MEASURED data, `auto-chain:` ticks, History `0 → 1` row. Click row → detail (mod/conf/SNR/BW/sha/source).
3. `Export PDF` writes a report file. Maximize/fullscreen → center tabs expand, sidebars keep width, no overlap.
4. Headless: `SIGNIT.exe --smoke --history-db <tmp>` prints `SMOKE OK` and exits 0 (synth BPSK/QPSK/16QAM/2FSK through REAL ingest+chain, every tab cycled offscreen, `_source=="live"`, `validate_demo` clean — see `production/app/main.py:94-120`).
5. Offline: disconnect network → everything still works. History persists at `%APPDATA%/SIGNIT/history.db` unless `--history-db` overrides.

## 6. Implementation plan (execute in order, stop on first red)

### 6.1 Staged install (PowerShell, repo root)

```powershell
py -3.10 -m pip install --upgrade pip setuptools wheel
py -3.10 -m pip install numpy==1.26.4
py -3.10 -m pip install pyldpc==0.7.7 --no-build-isolation
Get-Content production/requirements.txt | Where-Object { $_ -notmatch '^\s*pyldpc==' } | Set-Content $env:TEMP/requirements-nopyldpc.txt
py -3.10 -m pip install -r $env:TEMP/requirements-nopyldpc.txt
```

Verify: `py -3.10 -c "import numpy, scipy, sklearn, PySide6, onnxruntime, numba, pyfftw, soundfile, galois, commpy, pyldpc; print('deps ok')"`.

### 6.2 Train CNN (REQUIRED before release build, else CNN vote = pending)

Isolated env only — torch must NOT enter runtime env:

```powershell
py -3.10 -m venv .train-venv
.train-venv\Scripts\python -m pip install torch onnx numpy
.train-venv\Scripts\python -m ml.train_cnn
# working dir: production/ ; output: production/ml/models/signit_cnn.onnx (~2MB, gitignored)
dir production\ml\models\*.onnx
```

If you skip this, the exe still builds but ships WITHOUT model (fallback). For the PPT/finals release, DO train.

### 6.3 Tests + source smoke (must be green before build)

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest production/tests/ -q
$env:QT_QPA_PLATFORM = "offscreen"
python -m app.main --smoke --history-db "$env:TEMP/signit_smoke.db"
# working-directory for the second command: production/
# expect: SMOKE live=bpsk valid=True ... SMOKE OK: ...
```

10 test files must pass: `test_phase1-7, test_smoke, test_live_chain, test_hardening`. Fix code first if red — do not proceed to build.

### 6.4 Build exe

```powershell
pyinstaller production/signit.spec --noconfirm
# output: dist/SIGNIT.exe
if (-not (Test-Path "dist/SIGNIT.exe")) { throw "dist/SIGNIT.exe not produced" }
(Get-Item "dist/SIGNIT.exe").Length
```

Expect large single file (PySide6+SciPy+sklearn+onnxruntime+numba+matplotlib+pyFFTW+Qt; `upx=True` compresses; torch excluded). No size gate — record bytes for handoff.

### 6.5 Verify exe (headless + GUI)

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\SIGNIT.exe --smoke --history-db "$env:TEMP\signit_exe_smoke.db"
# expect SMOKE OK, exit 0
```

Then real GUI (needs display): `.\dist\SIGNIT.exe` → splash → READY → drop a 1–5MB `.wav` and an `.iq` (int16 default) → 6 tabs fill → history row → Export PDF → maximize check. Test on a CLEAN Windows machine without Python to prove single-file.

### 6.6 CI alternative (if local build fails)

Push any `production/**` change (or `workflow_dispatch`) triggers `.github/workflows/windows-build.yml` on `windows-latest`: checkout → Python 3.10 + pip cache → staged install (same as 6.1) → `pytest production/tests/ -q` → `python -m app.main --smoke` (cwd production) → `pyinstaller` → `dist/SIGNIT.exe --smoke` → upload artifact `SIGNIT-windows-exe`. Download from Actions → Artifacts. NOTE: CI does NOT train the CNN — for a live CNN vote, train locally (6.2) BEFORE pushing, or accept pending-vote. Do not commit `ml/models/*.onnx` (gitignored by design).

## 7. Publish for website download (GitHub Releases — REQUIRED)

Do NOT commit the exe to git or `prototype/frontend/public/` (100–300MB breaks clones + Vercel ~50MB limit). Use Releases:

```powershell
# from repo root, after verified dist/SIGNIT.exe
gh release create v0.1.0 dist/SIGNIT.exe --title "SIGNIT v0.1.0 (Windows exe)" --notes "Offline RF analyzer. Run SIGNIT.exe, drop .iq/.wav/.bin. Unsigned build: SmartScreen -> More info -> Run anyway."
# or via web: GitHub repo -> Releases -> Draft new release -> tag v0.1.0 -> Attach dist/SIGNIT.exe -> Publish
certutil -hashfile dist\SIGNIT.exe SHA256
```

Stable download URL shape: `https://github.com/<OWNER>/<REPO>/releases/download/v0.1.0/SIGNIT.exe`. Keep this exact file name (`SIGNIT.exe`) so the website button never breaks across versions (upload new version as `v0.2.0` with same asset name).

**Handoff back to web team (paste ALL five):** (1) Release download URL, (2) version tag, (3) file bytes, (4) SHA256 hex, (5) repo owner/name. Example: `https://github.com/akshanshuwu/signit_prototype/releases/download/v0.1.0/SIGNIT.exe | v0.1.0 | 182345678 bytes | SHA256:abc...`.

SmartScreen note for website copy: unsigned exe → Windows shows "Windows protected your PC" → click "More info → Run anyway". This is expected.

## 8. Troubleshooting (check first)

| Symptom | Fix |
|---|---|
| `pyldpc` build fails / numpy not found | Install numpy FIRST, then `pyldpc --no-build-isolation` (6.1 order). Never `pip install -r requirements.txt` in one shot on fresh env. |
| `numba 0.60 unsatisfiable` / galois error | Pin `numba==0.59.1` exactly; do not upgrade. |
| CNN vote `pending` | `ml/models/*.onnx` absent at build time → train (6.2) and rebuild. Spec bundles WHEN PRESENT only. |
| Qt platform plugin / display error in smoke | Set `$env:QT_QPA_PLATFORM="offscreen"` for ALL headless commands (tests + both smokes). |
| History DB locked / permission | Always pass explicit `--history-db $env:TEMP\*.db` in CI/smoke. Default writes `%APPDATA%/SIGNIT/history.db`. |
| `dist/SIGNIT.exe` missing | Run pyinstaller from REPO ROOT with path `production/signit.spec --noconfirm`; check `pyinstaller==6.9.0` installed. |
| Exe runs on dev PC but not clean PC | Missing DLL from non-default dep — rebuild via CI `windows-latest` and test that artifact; do not hand-edit spec hiddenimports unless you add the missing package there AND in requirements. |
| Tests red | Fix `production/` code, re-run 6.3. Never ship an exe from red tests. |

## 9. Done checklist (paste results back)

- [ ] `git rev-parse HEAD` = `d2998db` (or later agreed SHA)
- [ ] `pytest production/tests/ -q` green (paste tail)
- [ ] `python -m app.main --smoke` → `SMOKE OK` (paste line)
- [ ] `ml/models/signit_cnn.onnx` present at build? yes/no (bytes)
- [ ] `dist/SIGNIT.exe` bytes + `exe --smoke` → `SMOKE OK`
- [ ] Clean-PC GUI check (splash, drop wav+iq, 6 tabs, history, PDF, maximize)
- [ ] GitHub Release URL + version + bytes + SHA256 handed to web team
