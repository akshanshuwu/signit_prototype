"""Intel PDF report — one-click export.

Renders a live ingest result into a single-file PDF: header + modulation
verdict + estimates + voter breakdown + bits preview + comparator +
mission log. Pure function over the frozen result contract — no Qt,
no network.
"""
from __future__ import annotations

import datetime


def _lines(demo: dict, log: list[str] | None = None) -> list[tuple[str, str]]:
    """(style, text) rows: style in {h1, h2, body, mono}."""
    meta, pred = demo["meta"], demo["predictions"]
    out: list[tuple[str, str]] = [
        ("h1", "SIGNIT — Signal Intelligence Report"),
        ("body", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"),
        ("body", f"File: {meta['file']} · fs {meta['fs']} Hz · center {meta.get('center_freq', 0)} Hz"),
        ("h2", "Verdict"),
        ("body", f"Modulation: {pred['modulation']} @ {pred['confidence']:.2f} confidence"),
        ("body", f"Symbol rate (est): {pred['symbol_rate_est']} sym/s · BW (est): {pred['bw_est']} Hz"),
        ("body", f"SNR (est): {pred['snr_est']:.1f} dB · Fs: {pred['fs_est']} Hz"),
        ("h2", "Voter breakdown"),
    ]
    for key, val in pred["votes"].items():
        out.append(("body", f"{key}: {val}"))
    try:
        from ml.explain import explain_line_from_votes

        out.append(("body", explain_line_from_votes(pred["votes"])))
    except Exception:
        pass
    bp = demo["bits_preview"]
    out += [
        ("h2", "Bits preview"),
        ("mono", f"hex: {bp['hex'][:160]}"),
        ("mono", f"ascii: {bp['ascii'][:120]}"),
        ("body", f"sync corr peak: lag {bp['corr_peak']['lag']} value {bp['corr_peak']['value']:.2f}"),
        ("h2", ".IQ vs .wav"),
        ("body", f"IQ SNR {demo['comparator']['iq_snr']:.1f} dB · wav SNR "
                 f"{demo['comparator']['wav_snr']:.1f} dB"),
        ("body", demo["comparator"]["note"]),
    ]
    if log:
        out.append(("h2", "Mission log"))
        out += [("mono", line) for line in log[-40:]]
    return out


def write_intel_pdf(demo: dict, path: str, log: list[str] | None = None) -> str:
    """Write the Intel PDF to path. Returns path. Raises on contract violation."""
    from app.demo_store import validate_demo

    errs = validate_demo(demo)
    if errs:
        raise ValueError(f"demo contract violations: {errs}")
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    kw = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}

    def chunks(text: str, width: int = 100) -> list[str]:
        """Hard-wrap long unbreakable tokens (hex/ascii runs) for FPDF."""
        words, out = text.split(" "), []
        for w in words:
            while len(w) > width:
                out.append(w[:width])
                w = w[width:]
            out.append(w)
        # re-wrap to width for tidy lines
        lines, cur = [], ""
        for w in out:
            if len(cur) + len(w) + 1 > width:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}" if cur else w
        if cur:
            lines.append(cur)
        return lines or [""]

    for style, text in _lines(demo, log):
        safe = text.encode("latin-1", "replace").decode("latin-1")
        parts = chunks(safe) if style == "mono" else [safe]
        if style == "h1":
            pdf.set_font("Helvetica", "B", 16)
            for part in parts:
                pdf.multi_cell(0, 9, part, **kw)
        elif style == "h2":
            pdf.set_font("Helvetica", "B", 12)
            pdf.ln(2)
            for part in parts:
                pdf.multi_cell(0, 8, part, **kw)
        elif style == "mono":
            pdf.set_font("Courier", "", 8)
            for part in parts:
                pdf.multi_cell(0, 4.5, part, **kw)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, safe, **kw)
    pdf.output(path)
    return path
