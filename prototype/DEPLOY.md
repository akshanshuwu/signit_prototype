# Deploy — SIGNIT Prototype to Vercel (frontend-only v1)

Takes ~10 min. No backend, no env vars required.

## 1. Push to GitHub
```bash
git init  # if needed
git add prototype/frontend prototype/PRD.md prototype/IMPLEMENTATION_PLAN.md TECH_STACK.md
git commit -m "SIGNIT prototype v1: frontend-only 4-sample demo"
git branch -M main
git remote add origin <your-github-url>
git push -u origin main
```

## 2. Import to Vercel
1. Go to vercel.com → Add New → Project → import your repo.
2. Framework Preset: Next.js (auto-detected).
3. **Root Directory: `prototype/frontend`** (required — repo root has no package.json).
4. Node version: 18 (default OK; built locally on Node 25, Vercel builds with 18 fine).
5. No environment variables needed for v1.
6. Deploy → wait ~2 min → you get `https://<app>.vercel.app`.

## 3. Verify live link (must pass before PPT)
- `https://<app>.vercel.app/` → landing loads
- `https://<app>.vercel.app/analyze` → upload + 4 samples
- `https://<app>.vercel.app/analyze/qpsk` (and bpsk/qam16/fsk2) → all 6 tabs render
- Incognito + phone check. If a tab is blank, hard-refresh (Plotly CDN-free bundle, no external calls).

## 4. Rollback
Vercel → Deployments → previous deployment → Promote to Production. PPT QR stays on `/analyze` (stable route).

## Notes
- Demo JSONs total 432KB, served statically — no cold starts, link never sleeps.
- `prototype/backend/` is NOT deployed in v1. `prototype/tools/gen_demos.py` is local-only.
- Next 14.2.5 shows a security notice upstream; fine for prototype, upgrade before any production reuse.
