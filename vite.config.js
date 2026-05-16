import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (id.includes("recharts")) return "recharts";
          if (id.includes("react-router")) return "react-vendor";
          if (id.includes("react-dom")) return "react-vendor";
          if (id.includes("node_modules/react/")) return "react-core";
          if (id.includes("i18next")) return "i18n";
          if (id.includes("axios")) return "axios";
        },
      },
    },
  },
});
