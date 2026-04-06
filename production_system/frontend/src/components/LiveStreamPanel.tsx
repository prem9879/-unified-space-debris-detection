import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://127.0.0.1:8000/api/v1/streams/live";

type LiveObject = { id: string; risk: number; velocity_km_s: number };

export function LiveStreamPanel(): JSX.Element {
  const [rows, setRows] = useState<LiveObject[]>([
    { id: "OBJ-001", risk: 0.62, velocity_km_s: 7.27 },
    { id: "OBJ-002", risk: 0.54, velocity_km_s: 8.37 },
    { id: "OBJ-003", risk: 0.24, velocity_km_s: 8.75 },
    { id: "OBJ-004", risk: 0.85, velocity_km_s: 8.88 },
    { id: "OBJ-005", risk: 0.49, velocity_km_s: 9.20 },
  ]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    try {
      const ws = new WebSocket(WS_URL);
      ws.onopen = () => setIsConnected(true);
      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { objects: LiveObject[] };
        setRows(payload.objects);
      };
      ws.onclose = () => setIsConnected(false);
      return () => ws.close();
    } catch {
      setIsConnected(false);
    }
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-3 border-b border-slate-700">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <span className="text-lg">🎯</span> Live Tracking Feed
        </h3>
        <motion.div animate={{ scale: isConnected ? 1 : 0.8 }} transition={{ repeat: isConnected ? Infinity : 0, repeatType: "reverse", duration: 1 }}>
          <span className={`inline-flex h-2 w-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-slate-500"}`} />
        </motion.div>
      </div>

      {/* Objects List */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {rows.map((row, idx) => (
          <motion.div
            key={row.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="group rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-700 hover:border-slate-600 p-3 transition-all cursor-pointer"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-white text-sm group-hover:text-cyan-300 transition-colors">{row.id}</span>
              <motion.span
                className={`px-2 py-1 rounded text-xs font-bold ${
                  row.risk > 0.7
                    ? "bg-red-950/50 text-red-300 border border-red-700/50"
                    : row.risk > 0.4
                      ? "bg-yellow-950/50 text-yellow-300 border border-yellow-700/50"
                      : "bg-emerald-950/50 text-emerald-300 border border-emerald-700/50"
                }`}
                animate={{ scale: row.risk > 0.7 ? [1, 1.05] : 1 }}
                transition={{ repeat: row.risk > 0.7 ? Infinity : 0, repeatType: "reverse", duration: 1 }}
              >
                {row.risk > 0.7 ? "🔴 HIGH" : row.risk > 0.4 ? "🟡 MED" : "🟢 LOW"}
              </motion.span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <p className="text-slate-400 mb-1">Velocity</p>
                <p className="text-cyan-300 font-semibold">{row.velocity_km_s.toFixed(2)} km/s</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Risk Score</p>
                <p className="text-orange-300 font-semibold">{(row.risk * 100).toFixed(1)}%</p>
              </div>
            </div>

            {/* Risk Indicator Bar */}
            <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${
                  row.risk > 0.7
                    ? "bg-gradient-to-r from-red-500 to-red-400"
                    : row.risk > 0.4
                      ? "bg-gradient-to-r from-yellow-500 to-yellow-400"
                      : "bg-gradient-to-r from-emerald-500 to-emerald-400"
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${row.risk * 100}%` }}
                transition={{ duration: 0.5, delay: idx * 0.05 }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Footer Stats */}
      <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-400 space-y-1">
        <div className="flex justify-between">
          <span>Objects tracked:</span>
          <span className="text-cyan-400 font-semibold">{rows.length}</span>
        </div>
        <div className="flex justify-between">
          <span>High-risk:</span>
          <span className="text-red-400 font-semibold">{rows.filter((r) => r.risk > 0.7).length}</span>
        </div>
      </div>
    </div>
  );
}
