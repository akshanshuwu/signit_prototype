# Frontend — Next.js + Tailwind + Plotly.js (Vercel)

Pages (App Router):
- `/` Landing (problem + workflow + .IQ vs .wav explainer)
- `/analyze` Drag-drop upload (`.iq/.wav/.bin`, up to 100MB) + fs/fc/dtype selects → inline results: 6 tabs (Spectrum | Waterfall | Constellation | Report | Compare | Bits) + Mission Log

Analysis: 100% in-browser DSP (`lib/dsp/` — parse, Welch PSD, STFT, estimators, bits preview, assembled by `toDemo.ts` into the `lib/analysis.ts` contract). No backend calls — `prototype/backend/` is untouched/undeployed, `NEXT_PUBLIC_API_URL` unused.

Deploy: import `prototype/frontend` as the Vercel project root (see `prototype/DEPLOY.md`). No env vars required.
