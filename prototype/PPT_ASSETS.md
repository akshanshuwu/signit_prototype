# PPT Assets — SIGNIT Prototype v1

## QR / Link
- QR target (stable): `https://<app>.vercel.app/analyze`
- Backup link on slide footer: `/analyze/qpsk` (best-looking sample).

## Screenshots to take (from localhost:3000 or live link)
1. `analyze/qpsk` → Report tab (QPSK 94% + confidence bar + Fs/symbol/BW/SNR grid).
2. `analyze/qpsk` → Waterfall tab (Viridis heatmap 128×64).
3. `analyze/qam16` → Constellation tab (16-point grid — most impressive).
4. Optional: Compare tab (IQ 14.8 dB vs wav 9.3 dB bars).

## Results table (paste on slide)
| Sample | Modulation | Confidence | Fs (est) | Symbol rate | SNR (est) |
|---|---|---|---|---|---|
| bpsk.iq | BPSK | 91% | 48000 Hz | 2000 sym/s | ~15.0 dB |
| qpsk.iq | QPSK | 94% | 48000 Hz | 2000 sym/s | ~14.8 dB |
| qam16.iq | 16QAM | 89% | 48000 Hz | 2000 sym/s | ~15.1 dB |
| fsk2.iq | 2FSK | 92% | 48000 Hz | 1000 sym/s | ~14.9 dB |

(Exact SNR values vary ±0.4 dB per generator seed; read yours from the Report tab.)

## Slide storyline (3 slides)
1. Problem → off-air .IQ/.wav needs auto parameter extraction (modulation, Fs, FEC…).
2. Demo → QR + 3 screenshots + table above. Line: “Live link, 4 samples, <3s load, no install.”
3. Roadmap → “Prototype (online samples) → Finals production (offline PySide6, any file, full FEC/interleaver brute-force, Intel PDF).”

##Honest scope line (for Q&A)
“v1 proves the full chain on precomputed samples. Random-file blind decode + full FEC ship in the offline production build.”
