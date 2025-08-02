export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ui: {
          bg: "#0b0b0f",
          card: "#141420",
          primary: "#7c3aed",
          primary2: "#a78bfa",
          accent: "#9333ea",
          border: "#1f1f2e",
          text: "#f8fafc",
          subtext: "#cbd5e1",
          danger: "#ef4444",
          success: "#10b981"
        }
      },
      borderRadius: { xl: "0.75rem", "2xl": "1rem" },
      boxShadow: { soft: "0 10px 30px rgba(0,0,0,0.35)" }
    }
  },
  plugins: []
}
