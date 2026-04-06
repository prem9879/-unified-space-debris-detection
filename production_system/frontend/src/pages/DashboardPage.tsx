import { useState, type ReactElement } from "react";
import { motion } from "framer-motion";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js";

import { LiveStreamPanel } from "../components/LiveStreamPanel";
import { OrbitScene } from "../components/OrbitScene";
import { fetchModels, fetchSLO, login, uploadDetection } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export function DashboardPage(): ReactElement {
  const [token, setToken] = useState<string>("");
  const [lastSummary, setLastSummary] = useState<string>("No detections yet");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [timeline, setTimeline] = useState<number>(50);
  const [modelCount, setModelCount] = useState<number>(0);
  const [sloP95, setSloP95] = useState<number>(0);

  const onLogin = async () => {
    const jwt = await login("analyst", "analyst123");
    setToken(jwt);
    const models = await fetchModels(jwt);
    setModelCount(models.models?.length ?? 0);
    const slo = await fetchSLO(jwt);
    setSloP95(slo.api_latency_ms_p95 ?? 0);
  };

  const onUpload = async (file: File) => {
    if (!token) return;
    const result = await uploadDetection(file, token);
    setLastSummary(`Frame ${result.frame_id} | Objects: ${result.detections.length} | FPS: ${result.fps_estimate}`);
  };

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 md:px-8" data-theme={theme}>
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-heading text-3xl">Space Debris Command Center</h1>
          <p className="text-sm text-cyan-100/80">Real-time multimodal intelligence for orbital safety</p>
        </div>
        <div className="flex gap-2">
          <button className="rounded-lg bg-slate-200 px-4 py-2 font-semibold text-slate-900" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            Theme: {theme}
          </button>
          <button className="rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-900" onClick={onLogin}>
            Analyst Login
          </button>
        </div>
      </header>

      <section className="grid gap-4 lg:grid-cols-2">
        <OrbitScene />
        <LiveStreamPanel />
      </section>

      <section className="mt-4 grid-cards">
        <motion.div className="panel p-4" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
          <h3 className="font-heading text-lg">Operational Snapshot</h3>
          <p className="mt-3 text-sm">Active model stack: {modelCount}</p>
          <p className="mt-1 text-sm">API p95 latency: {sloP95} ms</p>
        </motion.div>

        <motion.div className="panel p-4" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
          <h3 className="font-heading text-lg">Upload Image or Frame</h3>
          <input
            type="file"
            multiple
            className="mt-3 w-full rounded bg-slate-800 p-2"
            onChange={(e) => {
              const files = e.target.files;
              if (!files) return;
              Array.from(files).forEach((file) => {
                void onUpload(file);
              });
            }}
          />
          <div
            className="mt-3 rounded border border-dashed border-cyan-400/50 bg-slate-900/30 p-4 text-sm"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              Array.from(e.dataTransfer.files).forEach((file) => {
                void onUpload(file);
              });
            }}
          >
            Drag and drop images/videos here for batch analysis.
          </div>
          <p className="mt-3 text-sm text-cyan-100/80">{lastSummary}</p>
        </motion.div>

        <motion.div className="panel p-4" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <h3 className="font-heading text-lg">Detection Confidence Heat</h3>
          <Bar
            data={{
              labels: ["satellite_part", "rocket_body", "micrometeorite", "unknown"],
              datasets: [{
                label: "Confidence",
                data: [0.78, 0.66, 0.84, 0.42],
                backgroundColor: ["#39d2ff", "#60a5fa", "#34d399", "#f59e0b"],
              }],
            }}
            options={{ responsive: true, plugins: { legend: { labels: { color: "#dbeafe" } } }, scales: { y: { min: 0, max: 1 } } }}
          />
        </motion.div>

        <motion.div className="panel p-4" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <h3 className="font-heading text-lg">Trajectory Timeline</h3>
          <input
            type="range"
            min={0}
            max={100}
            value={timeline}
            className="mt-4 w-full"
            onChange={(e) => setTimeline(Number(e.target.value))}
          />
          <p className="mt-3 text-sm text-cyan-100/80">Playback position: {timeline}%</p>
        </motion.div>
      </section>
    </main>
  );
}
