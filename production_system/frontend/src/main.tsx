import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { LandingPage } from "./pages/LandingPage";
import { DashboardPage } from "./pages/DashboardPage";
import "./styles.css";

const queryClient = new QueryClient();

function App() {
  const [currentPage, setCurrentPage] = useState<"landing" | "dashboard">("landing");

  return (
    <QueryClientProvider client={queryClient}>
      {currentPage === "landing" ? (
        <LandingPage onNavigate={() => setCurrentPage("dashboard")} />
      ) : (
        <DashboardPage onNavigate={() => setCurrentPage("landing")} />
      )}
    </QueryClientProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
