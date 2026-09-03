# Frontend — Next.js + Tailwind + Plotly.js (Vercel)

Pages:
- `/` Landing (problem + workflow + .IQ vs .wav explainer)
- `/analyze` Drag-drop upload + Try Sample buttons
- `/results` Spectrum + Waterfall heatmap + Constellation scatter + Auto-report with confidence
- `/bits` Demod hex/ascii preview + correlation peak plot

Deploy: `vercel` from this folder only. API base URL via `NEXT_PUBLIC_API_URL` env.
Fallback: if backend unreachable, load from `../demo_jsons/*.json` for instant demo.
