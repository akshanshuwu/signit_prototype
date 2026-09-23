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
        ink: "#06090F",
        panel: "#0B1220",
        console: "#0A0F1A",
        line: "#1C2536",
        fog: "#8B98A9",
        paper: "#E6EDF3",
        signal: "#3DDC84",
        warn: "#F5A524"
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.03) inset, 0 12px 32px rgba(0,0,0,0.45)"
      }
    }
  },
  plugins: []
};
