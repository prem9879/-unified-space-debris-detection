import { useState, useEffect, type ReactElement } from "react";
import { motion } from "framer-motion";
import { Bar, Line, Doughnut, Radar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend, Filler, ArcElement, RadarController, RadialLinearScale } from "chart.js";

import { LiveStreamPanel } from "../components/LiveStreamPanel";
import { OrbitScene } from "../components/OrbitScene";
import { fetchModels, fetchSLO, login, uploadDetection } from "../services/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
  RadarController,
  RadialLinearScale
);

interface DashboardPageProps {
  onNavigate?: () => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps): ReactElement {
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
    if (!token) {
      await onLogin();
    }
    const formData = new FormData();
    formData.append("file", file);
    try {
      setUploadProgress(10);
      const result = await uploadDetection(token, formData);
      setUploadProgress(100);
      setLastSummary(`✓ Detected ${result.detections?.length ?? 0} objects in ${file.name}`);
      setTimeout(() => setUploadProgress(0), 2000);
    } catch (error) {
      console.error("Upload failed:", error);
      setLastSummary("Upload failed");
      setUploadProgress(0);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.15,
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
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-black">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Professional Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <div className="flex items-center justify-between gap-8">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-cyan-500/50">
                  ◆
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">Space Debris Command</h1>
                  <p className="text-xs text-slate-400 mt-0.5">AI-Powered Orbital Intelligence System</p>
                </div>
              </div>
            </motion.div>

            <motion.div className="flex items-center gap-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
              {/* Quick Stats */}
              <div className="hidden md:flex items-center gap-6 px-6 py-3 rounded-lg bg-slate-800/50 border border-slate-700">
                <div className="text-center">
                  <p className="text-xs text-slate-400">Active Threats</p>
                  <p className="text-lg font-bold text-orange-400">4</p>
                </div>
                <div className="w-px h-8 bg-slate-600"></div>
                <div className="text-center">
                  <p className="text-xs text-slate-400">Risk Level</p>
                  <p className="text-lg font-bold text-red-400">HIGH</p>
                </div>
              </div>

              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm font-medium transition-all"
              >
                {theme === "dark" ? "☀️" : "🌙"}
              </button>

              {onNavigate && (
                <button
                  onClick={onNavigate}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white text-sm font-medium transition-all shadow-lg shadow-cyan-500/30"
                >
                  🏠 Home
                </button>
              )}
            </motion.div>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-7xl px-6 py-8 z-10">
        {/* Top Section: Orbit + Live Feed + Threat Level */}
        <motion.div
          className="grid gap-6 lg:grid-cols-4 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Orbit Visualization */}
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <div className="rounded-2xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 overflow-hidden shadow-2xl hover:border-slate-600/50 transition-all h-96">
              <OrbitScene />
            </div>
          </motion.div>

          {/* Live Stream */}
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <div className="rounded-2xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 overflow-hidden shadow-2xl hover:border-slate-600/50 transition-all h-96">
              <LiveStreamPanel />
            </div>
          </motion.div>

          {/* Threat Assessment */}
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <div className="rounded-2xl bg-gradient-to-br from-red-950/40 to-slate-900/60 border border-red-700/30 p-6 shadow-2xl h-96 flex flex-col">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-2xl">⚠️</span> Threat Analysis
              </h3>
              <div className="flex-1 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-red-950/50 border border-red-700/50">
                    <p className="text-xs text-red-300 font-semibold">CRITICAL</p>
                    <p className="text-sm text-white mt-1">Collision Risk: 4.2%</p>
                  </div>
                  <div className="p-3 rounded-lg bg-yellow-950/50 border border-yellow-700/50">
                    <p className="text-xs text-yellow-300 font-semibold">HIGH</p>
                    <p className="text-sm text-white mt-1">Objects @ Risk: 12</p>
                  </div>
                  <div className="p-3 rounded-lg bg-blue-950/50 border border-blue-700/50">
                    <p className="text-xs text-blue-300 font-semibold">MONITORED</p>
                    <p className="text-sm text-white mt-1">Total Tracked: 428</p>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-700/50 text-center border border-slate-600">
                  <p className="text-xs text-slate-400 mb-1">Next Update</p>
                  <p className="text-lg font-bold text-cyan-400">2.3s</p>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* KPI Cards Row */}
        <motion.div
          className="grid gap-4 md:grid-cols-5 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {[
            { label: "Active Models", value: modelCount, icon: "🧠", color: "from-blue-600" },
            { label: "API Latency", value: sloP95.toFixed(0), unit: "ms", icon: "⚡", color: "from-cyan-600" },
            { label: "Detection Rate", value: 94.2, unit: "%", icon: "🎯", color: "from-emerald-600" },
            { label: "Objects Tracked", value: 428, icon: "📍", color: "from-purple-600" },
            { label: "System Uptime", value: 99.9, unit: "%", icon: "✓", color: "from-pink-600" },
          ].map((kpi, idx) => (
            <motion.div key={idx} variants={itemVariants}>
              <div className={`rounded-xl bg-gradient-to-br ${kpi.color} to-slate-800 p-5 border border-slate-700/50 shadow-lg hover:shadow-xl transition-all cursor-pointer group`}>
                <div className="flex items-start justify-between mb-3">
                  <p className="text-2xl">{kpi.icon}</p>
                  <div className="h-2 w-2 rounded-full bg-emerald-400 group-hover:animate-pulse"></div>
                </div>
                <p className="text-xs font-medium text-slate-300 mb-1">{kpi.label}</p>
                <div className="flex items-baseline gap-1">
                  <p className="text-2xl font-bold text-white">{kpi.value}</p>
                  {kpi.unit && <p className="text-xs text-slate-400">{kpi.unit}</p>}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Analytics Grid Row 1 */}
        <motion.div
          className="grid gap-6 lg:grid-cols-2 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Detection Distribution */}
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-green-400">📊</span> Detection Distribution
              </h3>
              <Doughnut
                data={{
                  labels: ["Satellite Parts", "Rocket Bodies", "Micrometeorites", "Unknown"],
                  datasets: [
                    {
                      data: [45, 28, 18, 9],
                      backgroundColor: [
                        "rgba(34, 197, 94, 0.8)",
                        "rgba(59, 130, 246, 0.8)",
                        "rgba(139, 92, 246, 0.8)",
                        "rgba(100, 116, 139, 0.8)",
                      ],
                      borderColor: "#1e293b",
                      borderWidth: 2,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  plugins: {
                    legend: {
                      position: "bottom" as const,
                      labels: { color: "#cbd5e1", padding: 15, font: { size: 12 } },
                    },
                  },
                }}
              />
            </div>
          </motion.div>

          {/* Collision Risk Matrix */}
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-orange-400">🔥</span> Collision Risk Matrix
              </h3>
              <div className="grid grid-cols-4 gap-2">
                {[
                  { risk: 0.12, label: "OBJ-001" },
                  { risk: 0.34, label: "OBJ-002" },
                  { risk: 0.56, label: "OBJ-003" },
                  { risk: 0.78, label: "OBJ-004" },
                  { risk: 0.23, label: "OBJ-005" },
                  { risk: 0.67, label: "OBJ-006" },
                  { risk: 0.45, label: "OBJ-007" },
                  { risk: 0.89, label: "OBJ-008" },
                ].map((item, idx) => (
                  <motion.div
                    key={idx}
                    className={`p-3 rounded-lg text-center cursor-pointer transition-all ${
                      item.risk > 0.7
                        ? "bg-red-950/50 border border-red-700/50"
                        : item.risk > 0.4
                          ? "bg-yellow-950/50 border border-yellow-700/50"
                          : "bg-emerald-950/50 border border-emerald-700/50"
                    }`}
                    whileHover={{ scale: 1.05 }}
                  >
                    <p className="text-xs font-bold text-slate-300">{item.label}</p>
                    <p className="text-lg font-bold mt-1">
                      {item.risk > 0.7 ? "🔴" : item.risk > 0.4 ? "🟡" : "🟢"}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">{(item.risk * 100).toFixed(0)}%</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Analytics Grid Row 2 */}
        <motion.div
          className="grid gap-6 lg:grid-cols-3 mb-8"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Upload Panel */}
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all h-full flex flex-col">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-cyan-400">📤</span> Quick Upload
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
                className={`flex-1 rounded-xl border-2 border-dashed transition-all flex items-center justify-center p-6 cursor-pointer ${
                  dragging
                    ? "border-cyan-400 bg-cyan-400/10 scale-105"
                    : "border-slate-600 bg-slate-900/50 hover:border-slate-500"
                }`}
              >
                <div className="text-center">
                  <p className="text-4xl mb-2">🛰️</p>
                  <p className="text-sm font-medium text-slate-300">Drop files here</p>
                  <p className="text-xs text-slate-500 mt-1">or click below</p>
                </div>
              </div>

              <label className="mt-4 px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold cursor-pointer hover:shadow-lg hover:shadow-cyan-500/50 transition-all text-center group">
                Browse Files
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
                  <p className="text-xs text-slate-400 mt-2 text-center">{uploadProgress}% Complete</p>
                </motion.div>
              )}

              <p className="mt-4 text-xs text-slate-400 flex items-center gap-2">
                {uploadProgress === 100 ? <span className="text-emerald-400">✓</span> : <span className="text-slate-500">○</span>}
                {lastSummary}
              </p>
            </div>
          </motion.div>

          {/* Detection Confidence Chart */}
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-cyan-400">📈</span> Detection Confidence
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
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-purple-400">🎬</span> Trajectory Timeline
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-400">Playback Position</span>
                    <span className="text-sm font-bold text-cyan-400">{timeline.toFixed(0)}%</span>
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

                <div className="h-20 rounded-lg bg-slate-900/50 border border-slate-700 p-3">
                  <Line
                    data={{
                      labels: ["0m", "30m", "60m", "90m", "120m"],
                      datasets: [
                        {
                          label: "Altitude (km)",
                          data: [450, 455, 462, 458, 465],
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
                        y: { display: false, min: 440, max: 470 },
                        x: { display: false },
                      },
                    }}
                  />
                </div>

                <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-700/30">
                  <p className="text-xs text-blue-300">Predicted Position</p>
                  <p className="text-sm text-white font-semibold mt-1">Lat: 45.2° | Long: 112.8°</p>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Bottom Row: Performance + Alerts */}
        <motion.div
          className="grid gap-6 lg:grid-cols-2"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Performance Metrics */}
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-green-400">⚡</span> Performance
              </h3>
              <div className="space-y-4">
                {[
                  { label: "Image Detection", value: 92, max: 100, icon: "🖼️" },
                  { label: "Video FPS", value: 30, max: 33, icon: "🎬" },
                  { label: "API Response", value: 164, max: 200, icon: "📡" },
                ].map((metric, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-slate-400">{metric.icon} {metric.label}</span>
                      <span className="text-sm font-bold text-emerald-400">{metric.value}ms</span>
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
              <div className="mt-6 p-4 rounded-lg bg-emerald-950/30 border border-emerald-700/30">
                <p className="text-xs text-emerald-300 font-semibold">✓ ALL SLA TARGETS MET</p>
                <p className="text-sm text-white mt-1">99.9% uptime maintained</p>
              </div>
            </div>
          </motion.div>

          {/* Active Alerts Panel */}
          <motion.div variants={itemVariants}>
            <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 shadow-lg hover:border-slate-600/50 transition-all">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-orange-400">🔔</span> System Alerts ({4})
              </h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {[
                  { title: "CRITICAL: Collision Risk Detected", time: "1 min ago", severity: "critical", obj: "OBJ-004" },
                  { title: "HIGH: Debris Trajectory Change", time: "5 min ago", severity: "high", obj: "OBJ-006" },
                  { title: "MEDIUM: Model Update Available", time: "12 min ago", severity: "medium", obj: "YOLOv8-8.3" },
                  { title: "INFO: Tracking Update Received", time: "2 hours ago", severity: "info", obj: "TLE-Catalog" },
                ].map((alert, idx) => (
                  <motion.div
                    key={idx}
                    className={`p-3 rounded-lg border-l-4 cursor-pointer transition-all ${
                      alert.severity === "critical"
                        ? "bg-red-950/30 border-red-700 border-l-red-500"
                        : alert.severity === "high"
                          ? "bg-yellow-950/30 border-yellow-700 border-l-yellow-500"
                          : alert.severity === "medium"
                            ? "bg-blue-950/30 border-blue-700 border-l-blue-500"
                            : "bg-slate-900/30 border-slate-700 border-l-slate-500"
                    }`}
                    whileHover={{ x: 2 }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-white">{alert.title}</p>
                        <p className="text-xs text-slate-400 mt-1">{alert.time} • {alert.obj}</p>
                      </div>
                      <span className="text-xs font-bold text-slate-500 ml-2">{alert.severity.toUpperCase()}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
