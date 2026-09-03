# SIGNIT Prototype — PRD v1 (Frontend-Only, Locked)

> Locked: frontend-only v1, 4 precomputed samples, solo, 2–3 days. No backend. Vercel only.

## 1. Overview
SIGINT demo website for SIH PPT screening. Judge opens Vercel link, clicks a sample, sees full signal intel in <30s. No install, never sleeps, works incognito/mobile.

Problem proven: raw `.IQ`/`.wav` off-air captures need automated modulation / Fs / symbol-rate / SNR estimation plus spectrum / waterfall / constellation proof plus bits preview, instead of manual inspection.

## 2. Goals / Non-Goals
Goals:
- Live link + QR in PPT that always works.
- 4 one-click demos (BPSK / QPSK / 16QAM / 2FSK) with full results.
- DRDO-serious dark ops look, not a simple student plot.
- Random upload handled gracefully as Demo Mode, no false claims.

Non-Goals (v1):
- No real blind decode of arbitrary files, no FastAPI deploy, no ONNX training, no full FEC (Viterbi / RS / LDPC brute-force), no files >15MB, no live SDR, no login / cloud / DB.

## 3. Users
Primary: SIH evaluator (2-min click test). Secondary: owner (PPT demo). No login.

## 4. User Stories + Acceptance Criteria
1. Open `/` and understand problem + `.IQ` vs `.wav` in 20s → hero + 3 cards + workflow strip + CTA to `/analyze`.
2. Click `Try QPSK.IQ` on `/analyze` → results in <3s from `public/demo/qpsk.json`, all tabs render, no console error.
3. Verify intel → ReportCard shows modulation + confidence bar + Fs / symbol / BW / SNR + votes (CNN / cumulants values come from JSON, mocked for v1).
4. See proof → Spectrum (PSD line 512 pts), Waterfall (heatmap 128x64), Constellation (≤2000 pts scatter), Bits (hex / ascii + correlation peak).
5. See differentiator → Compare tab shows `.IQ` vs `.wav` SNR + one-line note on phase/BW loss.
6. Drop random file → banner: “Prototype demo mode — showing sample result. Full blind decode in production.” Small `.wav` may show optional browser spectrum preview; otherwise blocked with message. Never crashes.

## 5. Functional Requirements
### Pages
- `/` Landing: header, hero (title + 1 line + 2 CTAs), stats strip, `.IQ` vs `.wav` cards, pipeline diagram (Upload → Estimate → Classify → Demod → Bits), footer.
- `/analyze`: UploadBox (drag-drop `.iq/.wav/.bin`, <15MB client check, fs/fc/dtype display only) + 4 Sample cards + Demo Mode notice.
- `/analyze/[id]` Results: tab bar (Spectrum | Waterfall | Constellation | Report | Compare | Bits) + mini Mission Log (static logs from JSON meta) + back button.

### Components (props from JSON only)
`UploadBox, SpectrumPlot(freqs, mags_db), WaterfallPlot(times, freqs, z_db), ConstellationPlot(i, q), ReportCard(predictions), Comparator(comparator), BitsView(hex, ascii, corr_peak)`.

### Data contract
`frontend/public/demo/*.json`: meta, predictions, psd (512), spectrogram (128x64), constellation (≤2000), bits_preview, comparator. Types frozen in `lib/demo.ts`. No DSP in browser except optional small `.wav` preview.

## 6. Design / UX
Dark theme (#0a0f1e bg, cyan/green accents), Tailwind, `plotly.js-dist-min` via dynamic import. Mobile responsive (plots stack). Loading skeleton, empty-state for bad file.

## 7. Performance / Constraints
- Each JSON 200–400KB, page <3s on 4G, `npm run build` passes on Node 18.
- Frontend-only, no secrets, no required backend calls. Try local JSON first for PPT reliability.
- Latest Chrome / Edge.

## 8. Verification Checklist (must pass before PPT)
- [ ] Incognito link opens, 4 samples each load all tabs, no console error.
- [ ] Lighthouse >80, phone renders, random drop shows banner not crash, QR scans to `/analyze`.

## 9. Risks
Plotly weight → code-split + dist-min. JSON too large → decimate. Evaluator tests 2GB file → Demo Mode banner. Vercel build fail → pinned deps.

## 10. PPT + Future
PPT: QR + 3 screenshots (waterfall, constellation, report) + 4-row table + roadmap slide “Prototype (online samples) → Production (offline any-file + full FEC / PDF)”.
v2 (if time): optional FastAPI `/analyze` for <15MB real decode. Production (finals): separate PySide6 build from scratch, no code sharing contract.
