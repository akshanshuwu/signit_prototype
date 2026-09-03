# SIGNIT - LOCKED TECH STACK (do not change without owner approval)

> Locked on 2026-09-03. Do not change until owner explicitly says to change.

## 1. PROTOTYPE (Online, for PPT link)
Purpose: clickable link in SIH PPT, no install, testable by anyone.

- Frontend: Next.js + Tailwind CSS + Plotly.js (deployed on Vercel)
  - Pages: Landing (problem + workflow + .IQ vs .wav explainer) / Analyze (drag-drop + Try Sample buttons) / Results (Spectrum, Waterfall, Constellation, Auto-report with confidence) / Bits (demod hex/ascii preview + correlation peak)
- Backend: FastAPI + Uvicorn (deployed on Render / HuggingFace Spaces)
  - Endpoints: POST /analyze, POST /demodulate, POST /decode, GET /demo/{id}
  - Limits: <15MB uploads, 10s timeout safe, decimated JSON (psd, spectrogram, constellation ~5k points)
- DSP (light): Python 3.10 + NumPy + SciPy + SoundFile + Matplotlib (headless)
  - .wav via soundfile/scipy.io.wavfile, .IQ via np.fromfile (fixed int16/float32 interleaved I/Q + user fs/fc)
- ML (light): scikit-learn (cumulants + RandomForest/SVM) + ONNX Runtime (small CNN exported from PyTorch, trained on RadioML + synthetic)
- Resilience: Instant Demo Mode with 4 precomputed JSONs (BPSK/QPSK/16QAM/2FSK) bundled in frontend for Render cold-start fallback
- What it proves: pipeline works end-to-end on small/known files. No 2GB files, no full LDPC/Viterbi brute-force, FEC shown as candidate ranking only.

## 2. PRODUCTION (Offline, for Finals)
Purpose: DRDO-grade desktop tool, any random file, 100% offline, no data leak, single .exe.

- GUI: PySide6 + pyqtgraph + Qt-Material Dark (ops console, no landing page fluff)
  - Layout: left file+params, center Spectrum/Waterfall/Constellation/Time tabs with ROI select, right Auto-Report + confidence, bottom Mission Log terminal
- Engine: in-process Python, direct calls (no HTTP)
  - Core: Python 3.10 + NumPy + pyFFTW (3x FFT) + SciPy + Numba (@jit for Viterbi/deinterleave/correlate) + numpy.memmap + QThreadPool (GUI never freezes)
  - Ingest: memmap chunked viewer, common complex64 + fs/fc struct, format selector for dtype
  - Estimators: welch/spectrogram/hilbert, cyclostationary peak, Gardner timing, carrier FFT, SNR/BW with visual proofs (eye diagram, correlation plots)
  - Demod: FSK/PSK/QAM via NumPy/commpy (Costas/PLL simplified)
  - De-interleave: Block/Convolutional/Diagonal/Pseudo-Random (custom NumPy, try-all + rank by BER)
  - FEC: galois (RS) + scikit-commpy (Conv/Viterbi) + pyldpc (LDPC) + concatenated wrappers
  - Bits: numpy.correlate sync-word/header finder, hex/ascii viewer, header/payload splitter, hash for chain-of-custody
- ML: PyTorch train -> ONNX export -> onnxruntime infer (<20ms CPU) + sklearn vote ensemble + attention heatmap for explainability
- Packaging: PyInstaller single binary + conda env + requirements.txt pinned, Docker fallback, SQLite local only
- Data-gen only: GNU Radio Companion to synthesize demo .IQ/.wav, NOT a runtime dependency

## Separation rule
- prototype/ and production/ are fully separate and independent. They share nothing.
- Duplication of DSP/ML logic allowed. Optimize each for its own platform.
- No shared folder, no copy contract, no purity rules across projects.

## Standout differentiators (both, full in production)
1. One-click Auto-Chain with per-stage confidence ticks
2. .IQ vs .wav comparator (spectral relationship / degradation metric)
3. Explainable AI (CNN + cumulants vote + attention map)
4. Waterfall ROI re-analysis, impairment sliders, one-click Intel PDF report
