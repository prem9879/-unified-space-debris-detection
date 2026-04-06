import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { motion } from "framer-motion";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js";
import { LiveStreamPanel } from "../components/LiveStreamPanel";
import { OrbitScene } from "../components/OrbitScene";
import { fetchModels, fetchSLO, login, uploadDetection } from "../services/api";
ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);
export function DashboardPage() {
    const [token, setToken] = useState("");
    const [lastSummary, setLastSummary] = useState("No detections yet");
    const [theme, setTheme] = useState("dark");
    const [timeline, setTimeline] = useState(50);
    const [modelCount, setModelCount] = useState(0);
    const [sloP95, setSloP95] = useState(0);
    const onLogin = async () => {
        const jwt = await login("analyst", "analyst123");
        setToken(jwt);
        const models = await fetchModels(jwt);
        setModelCount(models.models?.length ?? 0);
        const slo = await fetchSLO(jwt);
        setSloP95(slo.api_latency_ms_p95 ?? 0);
    };
    const onUpload = async (file) => {
        if (!token)
            return;
        const result = await uploadDetection(file, token);
        setLastSummary(`Frame ${result.frame_id} | Objects: ${result.detections.length} | FPS: ${result.fps_estimate}`);
    };
    return (_jsxs("main", { className: "mx-auto max-w-7xl px-4 py-6 md:px-8", "data-theme": theme, children: [_jsxs("header", { className: "mb-6 flex flex-wrap items-center justify-between gap-3", children: [_jsxs("div", { children: [_jsx("h1", { className: "font-heading text-3xl", children: "Space Debris Command Center" }), _jsx("p", { className: "text-sm text-cyan-100/80", children: "Real-time multimodal intelligence for orbital safety" })] }), _jsxs("div", { className: "flex gap-2", children: [_jsxs("button", { className: "rounded-lg bg-slate-200 px-4 py-2 font-semibold text-slate-900", onClick: () => setTheme(theme === "dark" ? "light" : "dark"), children: ["Theme: ", theme] }), _jsx("button", { className: "rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-900", onClick: onLogin, children: "Analyst Login" })] })] }), _jsxs("section", { className: "grid gap-4 lg:grid-cols-2", children: [_jsx(OrbitScene, {}), _jsx(LiveStreamPanel, {})] }), _jsxs("section", { className: "mt-4 grid-cards", children: [_jsxs(motion.div, { className: "panel p-4", initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 }, children: [_jsx("h3", { className: "font-heading text-lg", children: "Operational Snapshot" }), _jsxs("p", { className: "mt-3 text-sm", children: ["Active model stack: ", modelCount] }), _jsxs("p", { className: "mt-1 text-sm", children: ["API p95 latency: ", sloP95, " ms"] })] }), _jsxs(motion.div, { className: "panel p-4", initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 }, children: [_jsx("h3", { className: "font-heading text-lg", children: "Upload Image or Frame" }), _jsx("input", { type: "file", multiple: true, className: "mt-3 w-full rounded bg-slate-800 p-2", onChange: (e) => {
                                    const files = e.target.files;
                                    if (!files)
                                        return;
                                    Array.from(files).forEach((file) => {
                                        void onUpload(file);
                                    });
                                } }), _jsx("div", { className: "mt-3 rounded border border-dashed border-cyan-400/50 bg-slate-900/30 p-4 text-sm", onDragOver: (e) => e.preventDefault(), onDrop: (e) => {
                                    e.preventDefault();
                                    Array.from(e.dataTransfer.files).forEach((file) => {
                                        void onUpload(file);
                                    });
                                }, children: "Drag and drop images/videos here for batch analysis." }), _jsx("p", { className: "mt-3 text-sm text-cyan-100/80", children: lastSummary })] }), _jsxs(motion.div, { className: "panel p-4", initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.1 }, children: [_jsx("h3", { className: "font-heading text-lg", children: "Detection Confidence Heat" }), _jsx(Bar, { data: {
                                    labels: ["satellite_part", "rocket_body", "micrometeorite", "unknown"],
                                    datasets: [{
                                            label: "Confidence",
                                            data: [0.78, 0.66, 0.84, 0.42],
                                            backgroundColor: ["#39d2ff", "#60a5fa", "#34d399", "#f59e0b"],
                                        }],
                                }, options: { responsive: true, plugins: { legend: { labels: { color: "#dbeafe" } } }, scales: { y: { min: 0, max: 1 } } } })] }), _jsxs(motion.div, { className: "panel p-4", initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.2 }, children: [_jsx("h3", { className: "font-heading text-lg", children: "Trajectory Timeline" }), _jsx("input", { type: "range", min: 0, max: 100, value: timeline, className: "mt-4 w-full", onChange: (e) => setTimeline(Number(e.target.value)) }), _jsxs("p", { className: "mt-3 text-sm text-cyan-100/80", children: ["Playback position: ", timeline, "%"] })] })] })] }));
}
