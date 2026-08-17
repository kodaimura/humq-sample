import React from "react";
import ReactDOM from "react-dom/client";
import { loadRuntimeConfig } from "@lib/config";
import "./global.css";

await loadRuntimeConfig();

const [{ default: AppRouter }, { AuthProvider }, { OperationsProvider }] = await Promise.all([
  import("./AppRouter"),
  import("./contexts/AuthContext"),
  import("./contexts/OperationsContext"),
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <OperationsProvider>
        <AppRouter />
      </OperationsProvider>
    </AuthProvider>
  </React.StrictMode>,
);
