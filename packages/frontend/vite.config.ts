import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// dev: 백엔드(8000)로 API·WebSocket 프록시 (CORS 회피)
const BACKEND = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/jobs": BACKEND,
      "/quota": BACKEND,
      "/health": BACKEND,
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
