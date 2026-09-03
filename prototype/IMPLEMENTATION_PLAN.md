# SIGNIT Prototype — Detailed Implementation Plan v1 (Frontend-Only)

> Locked: Next.js App Router + TypeScript + Tailwind + Plotly.js on Vercel only. Solo, 2–3 days. 4 precomputed samples. 1 copy only in `frontend/public/demo/`. No backend deploy. Python used once locally to generate JSONs.

## 0. Exit Criteria
- `https://<app>.vercel.app/analyze` opens incognito, 4 samples load all tabs in <3s, no backend env needed.
- `npm run build` passes, Lighthouse >80, phone renders, random drop shows Demo Mode banner.
- PPT has QR + 3 screenshots + 4-row table.

## 1. File Tree (to scaffold on approval, not yet built)
```
prototype/frontend/
  package.json (next 14, react 18, plotly.js-dist-min, tailwindcss, typescript)
  next.config.js, tailwind.config.js, tsconfig.json, .gitignore, vercel.json (rootDirectory=prototype/frontend — set in Vercel UI instead)
  .env.example (no required vars for v1)
  app/layout.tsx (dark shell + header + metadata)
  app/page.tsx (Landing)
  app/analyze/page.tsx (Upload + 4 samples)
  app/analyze/[id]/page.tsx (Results tabs)
  components/UploadBox.tsx, SpectrumPlot.tsx, WaterfallPlot.tsx, ConstellationPlot.tsx, ReportCard.tsx, Comparator.tsx, BitsView.tsx, MissionLog.tsx
  lib/demo.ts (types + loadDemo(id) + format helpers)
  public/demo/bpsk.json, qpsk.json, qam16.json, fsk2.json (ONLY copy, 200–400KB each)
tools/gen_demos.py (local-only, NOT deployed; numpy+scipy → writes the 4 JSONs)
```

Note: existing `prototype/demo_jsons/` (central) will be REMOVED at scaffold time per locked decision B to avoid 2-copy confusion. `prototype/backend/` stays untouched/undeployed for v1.

## 2. Frozen JSON Contract (all pages + plots depend on this)
```json
{
  "meta": {"modulation":"QPSK","fs":48000,"symbol_rate":2000,"snr_db":15,"center_freq":0,"file":"qpsk.iq"},
  "predictions": {"modulation":"QPSK","confidence":0.94,"votes":{"CNN":0.94,"cumulants":"QPSK"},"fs_est":48000,"symbol_rate_est":2000,"bw_est":4000,"snr_est":14.8},
  "psd": {"freqs":[512 floats],"mags_db":[512 floats]},
  "spectrogram": {"times":[64],"freqs":[128],"z_db":[[128x64]]},
  "constellation": {"i":[≤2000],"q":[≤2000]},
  "bits_preview": {"hex":"A3 5F ... (32 bytes)","ascii":"HELLO ...","corr_peak":{"lag":128,"value":0.92,"lags":[...],"vals":[...]}},
  "comparator": {"iq_snr":14.8,"wav_snr":9.2,"note":".wav loses phase BW, constellation collapses"},
  "log": ["ingest ok: 24000 samples", "psd ok", "cnn=QPSK 0.94"]
}
```
`lib/demo.ts` types MUST match exactly. Changing shape later breaks all plots — freeze Day 1.

## 3. Sample Generation Spec (Build phase, local only)
- Params: fs=48kHz, fc=0 baseband, 0.5s, SNR 15dB, 2k sym/s.
- BPSK: 2000 symbols, RRC alpha 0.35 (approx with FIR or rectangular for v1).
- QPSK: 2000 symbols, same pulse.
- 16QAM: 2000 symbols, normalized average power.
- 2FSK: dev 2kHz, 1000 bits, continuous phase.
- PSD: `scipy.signal.welch(nperseg=1024)` → interp/decimate to 512 pts, dB, freqs centered.
- Spectrogram: `scipy.signal.spectrogram(nperseg=256, noverlap=192)` → resize/crop to 128 freq x 64 time, dB.
- Constellation: ideal symbols + AWGN at SNR, downsample to ≤2000 pts, no carrier recovery in v1 (ideal + noise is fine for demo).
- Bits: random bits → hex (first 32 bytes) + ascii (printable fallback `.`) + synthetic corr peak (triangular peak at lag 128, value 0.9–0.95).
- Comparator: `wav_snr = iq_snr - 5.5dB` fixed + canned note per modulation.
- Script writes 4 JSONs directly to `prototype/frontend/public/demo/`. Verify each 200–400KB and valid JSON.

## 4. UI Build Spec (per component, Plotly via dynamic import)
- `SpectrumPlot`: Scatter line, x freq kHz, y dB, hover, dark template, 512 pts.
- `WaterfallPlot`: Heatmap z=z_db, x=times, y=freqs, colorscale Viridis/Inferno toggle, 128x64.
- `ConstellationPlot`: Scattergl markers size 3, opacity 0.6, equal axes, ≤2000 pts.
- `ReportCard`: modulation label + confidence progress bar + grid (Fs, symbol-rate, BW, SNR) + votes table (CNN vs cumulants).
- `Comparator`: two mini stats + note; v1 static from JSON, no live compute.
- `BitsView`: mono hex block + ascii block + corr peak line plot (lags vs vals).
- `UploadBox`: drag-drop, extension + <15MB check, on any file → show Demo Mode banner + suggest sample (do NOT attempt decode in v1; optional: if `.wav` <2MB, browser-only FFT preview — cut if behind schedule).
- `MissionLog`: mono list from `log[]`.

## 5. Day-Wise Solo Plan (14–16h total)
### Day 1 (4–5h) — Scaffold + Landing + Deploy link
1. `npx create-next-app@latest frontend --typescript --tailwind --app` inside `prototype/`, install `plotly.js-dist-min`.
2. Write `app/layout.tsx`, `app/page.tsx`, `app/analyze/page.tsx` skeleton with dead buttons.
3. `lib/demo.ts` types (copy contract above), hand-write 1 dummy `public/demo/qpsk.json` (10 pts) to unblock UI.
4. Push to GitHub, import `prototype/frontend` to Vercel, verify public URL. STOP — link locked for PPT.

### Day 2 (5–6h) — All plots + wiring
1. Build 7 components with dynamic `plotly.js-dist-min`, wire `app/analyze/[id]/page.tsx` tabs to `loadDemo(id)`.
2. `npm run build` + fix TS errors, test 1 dummy sample end-to-end incognito.
3. Add Demo Mode banner + UploadBox validation (no decode yet).

### Day 3 (4–5h) — Real data + polish + PPT assets
1. Write + run `tools/gen_demos.py` (needs `pip install numpy scipy`), output 4 JSONs, verify sizes + shapes.
2. Polish Compare/Bits/MissionLog, mobile check, Lighthouse quick pass.
3. `vercel --prod`, test all 4 samples on phone, screenshot waterfall + constellation + report for PPT, paste QR link.

Cut list if behind: drop optional `.wav` browser preview, drop eye diagram, drop Viridis/Inferno toggle (fix Viridis).

## 6. Verification Commands (run each gate)
- `npm run build` (Day 1, Day 2, Day 3 — must pass).
- `npx tsc --noEmit` if build hides TS errors.
- Manual: incognito → `/analyze` → click each sample → 6 tabs render, no console error.
- Manual: drop random 20MB file → banner, no crash. Drop bad extension → error message.
- `python3 tools/gen_demos.py && ls -lh prototype/frontend/public/demo/` → 4 files 200–400KB each + `python3 -c "import json; [json.load(open(f)) for f in ...]"`.

## 7. Deploy Spec (Vercel only)
- Vercel project root: `prototype/frontend`. Framework: Next.js. Node: 18. No env vars required v1.
- No `vercel.json` needed if root set in UI; else `{ "rootDirectory": "prototype/frontend" }` at repo root — decide at scaffold time.
- Rollback: previous Vercel deployment kept; PPT QR points to `/analyze` (stable route).

## 8. Risks + Cuts
- Plotly bloat → dynamic import + dist-min only. Cut 3D/gl if tempted.
- Time overrun → cut in this order: wav preview → eye → comparator polish → mission log → landing animations. Never cut: 4 JSONs + 3 core plots + ReportCard.
-(JSON shape drift → freeze `lib/demo.ts` Day 1, generator must conform, no ad-hoc fields.
