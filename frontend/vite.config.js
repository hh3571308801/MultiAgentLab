import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Dev server proxies /api to the FastAPI backend on :8000,
// so no CORS changes are needed in the backend.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
