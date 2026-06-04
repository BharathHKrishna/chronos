import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/history": "http://localhost:8002",
      "/forecast": "http://localhost:8002",
      "/narrative": "http://localhost:8002",
      "/tile": "http://localhost:8002",
      // production: set VITE_API_BASE_URL=https://chronos-api-8ok9.onrender.com
    },
  },
});
