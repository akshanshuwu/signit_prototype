# Backend — FastAPI (Render / HF Spaces)

Endpoints:
- POST /analyze -> {psd, spectrogram, constellation, predictions}
- POST /demodulate -> {bits_preview, hex, ascii}
- POST /decode -> {fec_candidates ranked by BER}
- GET /demo/{id} -> precomputed result

Run locally: `uvicorn app:app --reload`
Deploy: Render free web service from this folder only.

DSP: self-contained in `dsp/`, optimized for web (small files, JSON out).
ML: self-contained in `ml/` (*.onnx + sklearn fallback), optimized for web.
Production will write its own independent engine optimized for desktop.
