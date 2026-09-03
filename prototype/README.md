# SIGNIT Prototype (Online, PPT link) — SELF-CONTAINED

Locked stack: Next.js + Tailwind + Plotly.js (Vercel) + FastAPI (Render/HF Spaces) + NumPy + SciPy + SoundFile + sklearn + onnxruntime.

This folder is fully self-contained and independent. Do NOT import from `../production`.
Production will be built separately from scratch. Duplicate logic if needed — no shared code contract.

## Layout (frontend-only v1)
- `frontend/` — Next.js App Router + TS, deploys to Vercel alone
- `frontend/public/demo/` — ONLY copy of 4 precomputed fallbacks (bpsk/qpsk/qam16/fsk2.json)
- `backend/` — untouched/undeployed for v1 (optional v2)
- `PRD.md`, `IMPLEMENTATION_PLAN.md` — frozen contracts

## Limits
- Uploads <15MB only, decimated JSON responses, FEC shown as candidate ranking
