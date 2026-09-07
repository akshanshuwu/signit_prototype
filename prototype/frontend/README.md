# Frontend — Next.js + Tailwind + Plotly.js (Vercel, frontend-only v1)

Pages (App Router):
- `/` Landing (problem + workflow + .IQ vs .wav explainer)
- `/analyze` Drag-drop upload (`.iq/.wav/.bin`, <15MB client check) + 4 Try Sample cards + Demo Mode notice
- `/analyze/[id]` Results: 6 tabs (Spectrum | Waterfall | Constellation | Report | Compare | Bits) + Mission Log + back button

Data: static `public/demo/*.json` (bpsk/qpsk/qam16/fsk2) loaded via `lib/demo.ts` `loadDemo(id)`. No backend calls in v1 — `prototype/backend/` is untouched/undeployed, `NEXT_PUBLIC_API_URL` unused.

Deploy: import `prototype/frontend` as the Vercel project root (see `prototype/DEPLOY.md`). No env vars required.
