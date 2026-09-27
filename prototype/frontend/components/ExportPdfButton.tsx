"use client";

import { useState } from "react";
import type { DemoJson } from "../lib/analysis";
import type { IQData } from "../lib/dsp/parse";
import { buildReportPdf } from "../lib/report-pdf";

/** Export to PDF — builds a real report from current results, then downloads it. */
export default function ExportPdfButton({
  demo,
  iq,
  mono,
}: {
  demo: DemoJson;
  iq: IQData;
  mono: Float32Array | null;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleExport() {
    if (busy) return;
    setBusy(true);
    setErr(null);
    try {
      // Let the loading state paint before the heavy render work.
      await new Promise((r) => setTimeout(r, 30));
      const { blob, filename } = await buildReportPdf({ demo, iq, mono });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch {
      setErr("Report failed — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="inline-flex shrink-0 items-center gap-2">
      {err && (
        <span role="alert" className="font-mono text-[11px] text-warn">
          {err}
        </span>
      )}
      <button
        type="button"
        onClick={handleExport}
        disabled={busy}
        aria-busy={busy}
        className="btn-primary rounded-md px-3 py-1.5 font-mono text-[11px] disabled:opacity-60"
      >
        {busy ? "GENERATING REPORT…" : "EXPORT TO PDF"}
      </button>
    </span>
  );
}
