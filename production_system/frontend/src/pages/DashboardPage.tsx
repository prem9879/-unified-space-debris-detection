import { useState, useEffect, type ReactElement } from "react";
import { motion } from "framer-motion";
import { Bar, Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend, Filler } from "chart.js";

import { LiveStreamPanel } from "../components/LiveStreamPanel";
import { OrbitScene } from "../components/OrbitScene";
import { fetchModels, fetchSLO, login, uploadDetection } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend, Filler);

export function DashboardPage(): ReactElement {
  const [token, setToken] = useState<string>("");
  const [lastSummary, setLastSummary] = useState<string>("Upload images to begin detection");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [timeline, setTimeline] = useState<number>(50);
  const [modelCount, setModelCount] = useState<number>(0);
  const [sloP95, setSloP95] = useState<number>(0);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);
  const [dragging, setDragging] = useState(false);

  // Auto-login on component mount
  useEffect(() => {
    const autoLogin = async () => {
      try {
        setIsLoading(true);
        const jwt = await login("analyst", "analyst123");
        setToken(jwt);
        const models = await fetchModels(jwt);
        setModelCount(models.models?.length ?? 0);
        const slo = await fetchSLO(jwt);
        setSloP95(slo.api_latency_ms_p95 ?? 0);
      } catch (error) {
        console.error("Auto-login failed:", error);
      } finally {
        setIsLoading(false);
      }
    };
    void autoLogin();
  }, []);

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
    setUploadProgress(30);
    try {
      const result = await uploadDetection(file, token);
      setUploadProgress(100);
      setLastSummary(`✓ Detected ${result.detections?.length ?? 0} objects | Confidence: ${(result.confidence_avg * 100).toFixed(1)}%`);
      setTimeout(() => setUploadProgress(0), 2000);
    } catch (error) {
      setLastSummary("✗ Detection failed");
      setUploadProgress(0);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { type: "spring", stiffness: 100, damping: 15 },
    },
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Professional Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white font-bold">
                  ◆
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Space Debris Command</h1>
                  <p className="text-xs text-slate-400">Real-time Orbital Intelligence System</p>
                </div>
              </div>
            </motion.div>

            <div className="flex items-center gap-4">
              <motion.div
                className="px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700 flex items-center gap-2 text-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                <span className={`h-2 w-2 rounded-full ${isLoading ? "bg-yellow-400 animate-pulse" : "bg-emerald-400"}`}></span>
                <span className="text-slate-300">{isLoading ? "Connecting..." : "System Ready"}</span>
              </motion.div>

              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm font-medium transition-all"
              >
                {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Top Row: Orbit visualization & Live Stream */}
        <motion.div
          className="grid gap-6 lg:grid-cols-3 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden shadow-2xl hover:border-slate-600/50 transition-all">
              <div className="h-96 bg-slate-900">
                <OrbitScene />
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants}>
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden shadow-2xl hover:border-slate-600/50 transition-all h-96">
              <LiveStreamPanel />
            </div>
          </motion.div>
        </motion.div>

        {/* KPI Cards Row */}
        <motion.div
          className="grid gap-4 md:grid-cols-4 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {[
            { label: "Active Models", value: modelCount, unit: "", color: "from-blue-500" },
            { label: "API Latency", value: sloP95, unit: "ms", color: "from-cyan-500" },
            { label: "Detection Rate", value: 94.2, unit: "%", color: "from-emerald-500" },
            { label: "System Uptime", value: 99.9, unit: "%", color: "from-purple-500" },
          ].map((kpi, idx) => (
            <motion.div key={idx} variants={itemVariants}>
              <div className={`rounded-lg bg-gradient-to-br ${kpi.color} to-slate-800 p-6 border border-slate-700/50 shadow-lg`}>
                <p className="text-sm font-medium text-slate-300 mb-2">{kpi.label}</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-white">{kpi.value}</p>
                  {kpi.unit && <p className="text-lg text-slate-400">{kpi.unit}</p>}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Main Content Grid */}
        <motion.div
          className="grid gap-6 lg:grid-cols-3 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Upload Panel */}
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all h-full flex flex-col">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-cyan-400">📤</span> Upload Detection
              </h3>

              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  Array.from(e.dataTransfer.files).forEach((file) => {
                    void onUpload(file);
                  });
                }}
                className={`flex-1 rounded-lg border-2 border-dashed transition-all flex items-center justify-center p-6 cursor-pointer ${
                  dragging
                    ? "border-cyan-400 bg-cyan-400/10 scale-105"
                    : "border-slate-600 bg-slate-900/50 hover:border-slate-500"
                }`}
              >
                <div className="text-center">
                  <p className="text-4xl mb-2">🛰️</p>
                  <p className="text-sm font-medium text-slate-300">Drop images/videos here</p>
                  <p className="text-xs text-slate-500 mt-1">Supports: FITS, RADAR, optical</p>
                </div>
              </div>

              <label className="mt-4 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-medium cursor-pointer hover:shadow-lg hover:shadow-cyan-500/50 transition-all text-center">
                Or click to browse
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => {
                    const files = e.currentTarget.files;
                    if (!files) return;
                    Array.from(files).forEach((file) => {
                      void onUpload(file);
                    });
                  }}
                />
              </label>

              {uploadProgress > 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4">
                  <div className="relative h-2 rounded-full bg-slate-700 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-cyan-400 to-blue-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-2">{uploadProgress}% processing</p>
                </motion.div>
              )}

              <p className="mt-4 text-sm text-slate-400 flex items-center gap-2">
                <span className={uploadProgress === 100 || !lastSummary.includes("Upload") ? "text-emerald-400" : "text-slate-500"}>
                  {uploadProgress === 100 || !lastSummary.includes("Upload") ? "✓" : "○"}
                </span>
                {lastSummary}
              </p>
            </div>
          </motion.div>

          {/* Detection Confidence Chart */}
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-blue-400">📊</span> Detection Confidence
              </h3>
              <Bar
                data={{
                  labels: ["Satellite", "Rocket", "Meteorite", "Unknown"],
                  datasets: [
                    {
                      label: "Confidence Score",
                      data: [0.94, 0.87, 0.92, 0.56],
                      backgroundColor: ["rgba(34, 197, 94, 0.8)", "rgba(59, 130, 246, 0.8)", "rgba(139, 92, 246, 0.8)", "rgba(100, 116, 139, 0.8)"],
                      borderRadius: 8,
                      borderSkipped: false,
                      borderColor: "rgba(255, 255, 255, 0.1)",
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: { display: false },
                  },
                  scales: {
                    y: {
                      min: 0,
                      max: 1,
                      ticks: { color: "#cbd5e1", stepSize: 0.2 },
                      grid: { color: "#334155" },
                    },
                    x: {
                      ticks: { color: "#cbd5e1" },
                      grid: { display: false },
                    },
                  },
                }}
              />
            </div>
          </motion.div>

          {/* Trajectory Timeline */}
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-purple-400">🎬</span> Trajectory Timeline
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-400">Playback</span>
                    <span className="text-sm font-semibold text-cyan-400">{timeline.toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={timeline}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                    onChange={(e) => setTimeline(Number(e.target.value))}
                  />
                </div>

                <div className="h-24 rounded-lg bg-slate-900/50 border border-slate-700 p-4 flex items-center justify-center">
                  <Line
                    data={{
                      labels: ["0s", "10s", "20s", "30s", "40s", "50s"],
                      datasets: [
                        {
                          label: "Trajectory",
                          data: [10, 15, 22, 18, 25, 20],
                          borderColor: "#06b6d4",
                          backgroundColor: "rgba(6, 182, 212, 0.1)",
                          fill: true,
                          tension: 0.4,
                          borderWidth: 2,
                          pointRadius: 0,
                        },
                      ],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: true,
                      plugins: { legend: { display: false } },
                      scales: {
                        y: { display: false },
                        x: { display: false },
                      },
                    }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Bottom Analytics Row */}
        <motion.div
          className="grid gap-6 lg:grid-cols-2"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Performance Metrics */}
          <motion.div variants={itemVariants}>
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-green-400">⚡</span> System Performance
              </h3>
              <div className="space-y-3">
                {[
                  { label: "Image Detection", value: 92, max: 100, unit: "ms" },
                  { label: "Video Processing", value: 30, max: 33, unit: "fps" },
                  { label: "API Response", value: 164, max: 200, unit: "ms p95" },
                ].map((metric, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-slate-400">{metric.label}</span>
                      <span className="text-sm font-semibold text-cyan-400">
                        {metric.value} {metric.unit}
                      </span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                        initial={{ width: 0 }}
                        animate={{ width: `${(metric.value / metric.max) * 100}%` }}
                        transition={{ duration: 1, delay: idx * 0.2 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Active Alerts */}
          <motion.div variants={itemVariants}>
            <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-orange-400">🔔</span> Active Alerts
              </h3>
              <div className="space-y-3">
                {[
                  { title: "High-Risk Debris Detected", time: "2 min ago", severity: "high" },
                  { title: "Collision Probability: 2.3%", time: "5 min ago", severity: "medium" },
                  { title: "Model Update Available", time: "1 hour ago", severity: "low" },
                ].map((alert, idx) => (
                  <div
                    key={idx}
                    className={`rounded-lg p-3 border border-l-4 ${
                      alert.severity === "high"
                        ? "bg-red-950/30 border-red-500 border-l-red-500"
                        : alert.severity === "medium"
                          ? "bg-yellow-950/30 border-yellow-600 border-l-yellow-500"
                          : "bg-blue-950/30 border-blue-600 border-l-blue-500"
                    }`}
                  >
                    <p className="text-sm font-medium text-white">{alert.title}</p>
                    <p className="text-xs text-slate-400 mt-1">{alert.time}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
