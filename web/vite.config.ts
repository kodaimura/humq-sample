import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@components": path.resolve(__dirname, "src/components"),
      "@layouts": path.resolve(__dirname, "src/components/layouts"),
      "@features": path.resolve(__dirname, "src/components/features"),
      "@ui": path.resolve(__dirname, "src/components/ui"),
      "@contexts": path.resolve(__dirname, "src/contexts"),
      "@pages": path.resolve(__dirname, "src/pages"),
      "@styles": path.resolve(__dirname, "src/styles"),
      "@lib": path.resolve(__dirname, "src/lib"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 3000,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./test/setup.ts",
  },
});
