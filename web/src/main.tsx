import React from "react";
import ReactDOM from "react-dom/client";
import { loadRuntimeConfig } from "@lib/config";
import "./global.css";

await loadRuntimeConfig();

const [{ default: AppRouter }, { AuthProvider }] = await Promise.all([
  import("./AppRouter"),
  import("./contexts/AuthContext"),
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>,
);
