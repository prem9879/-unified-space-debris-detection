import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/api/v1/streams/live";
export function LiveStreamPanel() {
    const [rows, setRows] = useState([]);
    useEffect(() => {
        const ws = new WebSocket(WS_URL);
        ws.onmessage = (event) => {
            const payload = JSON.parse(event.data);
            setRows(payload.objects);
        };
        return () => ws.close();
    }, []);
    return (_jsxs("div", { className: "panel p-4", children: [_jsx("h3", { className: "font-heading text-lg", children: "Live Tracking Feed" }), _jsx("div", { className: "mt-3 space-y-2", children: rows.map((row) => (_jsxs("div", { className: "flex items-center justify-between rounded-md bg-slate-900/50 px-3 py-2 text-sm", children: [_jsx("span", { children: row.id }), _jsxs("span", { children: [row.velocity_km_s.toFixed(2), " km/s"] }), _jsxs("span", { className: row.risk > 0.6 ? "text-orange-300" : "text-cyan-300", children: [(row.risk * 100).toFixed(1), "%"] })] }, row.id))) })] }));
}
