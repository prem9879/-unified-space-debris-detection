import { useEffect, useState } from "react";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/api/v1/streams/live";

type LiveObject = { id: string; risk: number; velocity_km_s: number };

export function LiveStreamPanel(): JSX.Element {
  const [rows, setRows] = useState<LiveObject[]>([]);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { objects: LiveObject[] };
      setRows(payload.objects);
    };
    return () => ws.close();
  }, []);

  return (
    <div className="panel p-4">
      <h3 className="font-heading text-lg">Live Tracking Feed</h3>
      <div className="mt-3 space-y-2">
        {rows.map((row) => (
          <div key={row.id} className="flex items-center justify-between rounded-md bg-slate-900/50 px-3 py-2 text-sm">
            <span>{row.id}</span>
            <span>{row.velocity_km_s.toFixed(2)} km/s</span>
            <span className={row.risk > 0.6 ? "text-orange-300" : "text-cyan-300"}>{(row.risk * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
