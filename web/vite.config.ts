import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          radix: [
            "@radix-ui/react-tabs",
            "@radix-ui/react-dialog",
            "@radix-ui/react-select",
            "@radix-ui/react-checkbox",
            "@radix-ui/react-tooltip",
          ],
        },
      },
    },
  },
  server: {
    proxy: { "/api": "http://127.0.0.1:8088" },
  },
});
