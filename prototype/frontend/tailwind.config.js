/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["ui-sans-system", "-apple-system", "Segoe UI", "Inter", "Roboto", "sans-serif"],
        display: ["Space Grotesk", "ui-sans-system", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "JetBrains Mono", "Menlo", "monospace"]
      },
      colors: {
        // Warm-white engineering theme. Key names kept so existing
        // classes (bg-ink, bg-panel, text-paper, ...) flip to light
        // without logic changes.
        ink: "#FAF8F4", // page canvas (was dark #06090F)
        canvas: "#FAF8F4", // alias for new code
        panel: "#FFFFFF", // cards (was dark #0B1220)
        console: "#F4EFE6", // tinted console/log wells (was #0A0F1A)
        line: "#E7E0D3", // subtle warm borders (was #1C2536)
        fog: "#6B7280", // muted text, darkened for light bg (was #8B98A9)
        muted: "#6B7280", // alias for new code
        paper: "#1A1E22", // primary text (was light #E6EDF3)
        signal: "#16A34A", // data green, contrast-safe on white (was #3DDC84)
        accent: "#0E7C6B", // links / primary actions
        warn: "#B45309", // amber, darkened for light bg (was #F5A524)
      },
      borderRadius: {
        lg: "12px",
        md: "10px",
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.6) inset, 0 12px 32px rgba(26,30,34,0.08)",
        card: "0 1px 2px rgba(26,30,34,0.06), 0 8px 24px rgba(26,30,34,0.06)",
        subtle: "0 1px 2px rgba(26,30,34,0.05)",
      }
    }
  },
  plugins: []
};
