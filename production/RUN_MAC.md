# Run SIGNIT Locally on macOS (no Windows needed)

The `SIGNIT.exe` file itself is Windows-only (built by the `windows-build`
GitHub Action on `windows-latest`), but the **exact same code** runs as a
desktop window on your Mac from source. Test everything here first.

## One command

```bash
cd production
./run_local.sh
```

This creates/uses `.venv` (Python 3.10, matches the `.exe` target),
installs deps staged (numpy → pyldpc `--no-build-isolation` → rest, same as
CI), then launches the GUI with a scratch history DB in `/tmp`.

## Manual steps (if the script isn't for you)

```bash
cd production
uv python install 3.10 && uv venv --python 3.10 .venv
.venv/bin/python -m ensurepip && .venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install "numpy==1.26.4" "scipy==1.13.1" "scikit-learn==1.5.1"
.venv/bin/python -m pip install --no-build-isolation "pyldpc==0.7.7"
.venv/bin/python -m pip install -r requirements.txt
```

## Headless sanity (no window)

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q
QT_QPA_PLATFORM=offscreen .venv/bin/python -m app.main --smoke --history-db /tmp/signit_smoke.db
```

## Real GUI (needs display — splash shows on macOS)

```bash
.venv/bin/python -m app.main --history-db /tmp/signit.db
# flags: --no-splash to skip splash, --history-db PATH to override the DB
```

## What to check

1. Splash `SIGNIT // RF SIGNAL ANALYZER` flashes, then an empty READY state
   (3-line prompt in Mission Log, report shows `UNKNOWN`).
2. Click `QPSK (live)` → title `synth:qpsk.iq`, measured QPSK + confidence,
   `auto-chain:` ticks, History panel `0 → 1` row.
3. Drop any `.iq/.wav/.bin` (or make one: synth a burst to `/tmp/real.iq`
   and Browse to it) → all 6 tabs fill with measured data, history grows.
4. Click a history row → detail line (mod/conf/SNR/BW/sha/source).
5. `Export PDF` writes a local report.
6. Prove not-hardcoded: quit, rename `assets/demo/` aside, relaunch —
   everything above still works (only explicit fallback needs the JSONs).

Default history DB (when `--history-db` is omitted): `~/.signit/history.db`
(Windows `.exe` uses `%APPDATA%/SIGNIT/history.db`).
