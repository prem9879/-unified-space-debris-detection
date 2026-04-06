export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${API_BASE}/healthz`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function uploadDetection(file: File, token: string): Promise<any> {
  const form = new FormData();
  form.append("modality", "optical");
  form.append("image", file);

  const res = await fetch(`${API_BASE}/api/v1/detection/infer`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  });

  if (!res.ok) throw new Error(`Detection failed: ${res.status}`);
  return res.json();
}

export async function fetchModels(token: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/models/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Model list failed");
  return res.json();
}

export async function fetchSLO(token: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/monitoring/slo`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("SLO snapshot failed");
  return res.json();
}

export async function login(username: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  const payload = await res.json();
  return payload.access_token;
}
