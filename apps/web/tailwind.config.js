/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        chronos: {
          bg: "#0f1117",
          panel: "#1a1d2e",
          border: "#2a2d3e",
          accent: "#4f8ef7",
          future: "#a855f7",
          past: "#22d3ee",
        },
      },
    },
  },
  plugins: [],
};
