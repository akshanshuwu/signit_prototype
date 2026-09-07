"""Explainable-AI helpers — Phase 7.

Turns a VoteResult (or a demo-dict votes section) into a human-readable
rationale: per-voter weighted contribution shares, the winning margin,
and why abstentions happened. Pure functions, no Qt — the ReportCard
renders the one-line summary, the Intel PDF the full block.
"""
from __future__ import annotations


def contributions(parts: dict, weights: dict) -> dict[str, float]:
    """Normalized contribution share per voter: w[v]*conf / total."""
    scores = {v: float(weights.get(v, 0.0)) * float(conf) for v, (_m, conf) in parts.items()}
    total = sum(scores.values())
    if total <= 0:
        return {v: 0.0 for v in parts}
    return {v: s / total for v, s in scores.items()}


def explain_vote(vote) -> list[str]:
    """Multi-line rationale for a VoteResult (winner, confidence, parts, note)."""
    parts = getattr(vote, "parts", {}) or {}
    if getattr(vote, "winner", "UNKNOWN") == "UNKNOWN" or not parts:
        return [f"AI vote: UNKNOWN — {getattr(vote, 'note', 'all voters abstained')}"]
    try:
        from ml.ensemble import WEIGHTS
    except ImportError:
        WEIGHTS = {}
    shares = contributions(parts, WEIGHTS)
    order = sorted(parts, key=lambda v: shares.get(v, 0.0), reverse=True)
    cells = ", ".join(
        f"{v} {parts[v][0]} {parts[v][1]:.2f}×{WEIGHTS.get(v, 0.0):.2f}={shares.get(v, 0.0):.0%}"
        for v in order
    )
    lines = [
        f"AI vote: {vote.winner} ({vote.confidence:.2f}; "
        f"{'all agree' if getattr(vote, 'agreed', False) else 'split decision'})",
        f"voter shares [{cells}]",
    ]
    note = getattr(vote, "note", "")
    if note:
        lines.append(note)
    return lines


def explain_line_from_votes(votes: dict) -> str:
    """One-line XAI summary from a demo-dict votes section (ReportCard use).

    Handles both bundled-demo shape ({CNN, cumulants}) and live shape
    ({CNN, cumulants, demod, ensemble}).
    """
    if not votes:
        return "AI: no votes yet"
    bits = []
    if "ensemble" in votes:
        bits.append(f"ensemble {votes['ensemble']:.2f}")
    for key in ("demod", "cumulants", "CNN"):
        if key in votes:
            bits.append(f"{key} {votes[key]}")
    return "AI: " + " · ".join(str(b) for b in bits)
