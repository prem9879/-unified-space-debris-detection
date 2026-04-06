export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
export const LEGACY_API_BASE = import.meta.env.VITE_LEGACY_API_BASE ?? "/legacy-api";
const LEGACY_API_KEY = import.meta.env.VITE_LEGACY_API_KEY ?? "";

function legacyHeaders(apiKey?: string): Record<string, string> {
  const headerKey = apiKey?.trim() || LEGACY_API_KEY;
  return headerKey ? { "X-API-Key": headerKey } : {};
}

async function parseLegacyResponse(res: Response): Promise<any> {
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = payload?.error ?? `Legacy API request failed: ${res.status}`;
    throw new Error(message);
  }
  return payload;
}

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

export async function legacyPredict(params: {
  opticalFile?: File | null;
  radarFile?: File | null;
  physics: string;
  imageSize: number;
  opticalBand: string;
  normalizeMode: string;
  apiKey?: string;
}): Promise<any> {
  const form = new FormData();
  if (params.opticalFile) form.append("optical", params.opticalFile);
  if (params.radarFile) form.append("radar", params.radarFile);
  form.append("physics", params.physics);
  form.append("image_size", String(params.imageSize));
  form.append("optical_band", params.opticalBand);
  form.append("normalize_mode", params.normalizeMode);

  const res = await fetch(`${LEGACY_API_BASE}/predict`, {
    method: "POST",
    headers: legacyHeaders(params.apiKey),
    body: form,
  });

  return parseLegacyResponse(res);
}

export async function legacyLoadAllPublicData(apiKey?: string): Promise<any> {
  const res = await fetch(`${LEGACY_API_BASE}/load_all_public_data`, {
    method: "POST",
    headers: legacyHeaders(apiKey),
  });
  return parseLegacyResponse(res);
}

export async function legacyPreviewNasaSolarflux(apiKey?: string): Promise<any> {
  const res = await fetch(`${LEGACY_API_BASE}/preview_nasa_solarflux`, {
    headers: legacyHeaders(apiKey),
  });
  return parseLegacyResponse(res);
}

export async function legacyPredictDataset(params: {
  datasetDir: string;
  modality: string;
  maxSamples: number;
  imageSize: number;
  opticalBand: string;
  normalizeMode: string;
  apiKey?: string;
}): Promise<any> {
  const form = new FormData();
  form.append("dataset_dir", params.datasetDir);
  form.append("modality", params.modality);
  form.append("max_samples", String(params.maxSamples));
  form.append("image_size", String(params.imageSize));
  form.append("optical_band", params.opticalBand);
  form.append("normalize_mode", params.normalizeMode);

  const res = await fetch(`${LEGACY_API_BASE}/predict_dataset`, {
    method: "POST",
    headers: legacyHeaders(params.apiKey),
    body: form,
  });

  return parseLegacyResponse(res);
}

export async function legacyDatasetInventory(folder: string, limit = 120, apiKey?: string): Promise<any> {
  const url = new URL(`${LEGACY_API_BASE}/dataset_inventory`, window.location.origin);
  url.searchParams.set("folder", folder);
  url.searchParams.set("limit", String(limit));

  const res = await fetch(url.toString(), {
    headers: legacyHeaders(apiKey),
  });

  return parseLegacyResponse(res);
}

export async function legacyPredictFile(params: {
  filePath: string;
  modality: string;
  imageSize: number;
  opticalBand: string;
  normalizeMode: string;
  apiKey?: string;
}): Promise<any> {
  const form = new FormData();
  form.append("file_path", params.filePath);
  form.append("modality", params.modality);
  form.append("image_size", String(params.imageSize));
  form.append("optical_band", params.opticalBand);
  form.append("normalize_mode", params.normalizeMode);

  const res = await fetch(`${LEGACY_API_BASE}/predict_file`, {
    method: "POST",
    headers: legacyHeaders(params.apiKey),
    body: form,
  });

  return parseLegacyResponse(res);
}

export async function legacyCalibrationReport(params: {
  datasetDir: string;
  modality: string;
  maxSamples: number;
  bins: number;
  imageSize: number;
  opticalBand: string;
  normalizeMode: string;
  apiKey?: string;
}): Promise<any> {
  const form = new FormData();
  form.append("dataset_dir", params.datasetDir);
  form.append("modality", params.modality);
  form.append("max_samples", String(params.maxSamples));
  form.append("bins", String(params.bins));
  form.append("image_size", String(params.imageSize));
  form.append("optical_band", params.opticalBand);
  form.append("normalize_mode", params.normalizeMode);

  const res = await fetch(`${LEGACY_API_BASE}/calibration_report`, {
    method: "POST",
    headers: legacyHeaders(params.apiKey),
    body: form,
  });

  return parseLegacyResponse(res);
}

export async function legacyReadyz(apiKey?: string): Promise<any> {
  const res = await fetch(`${LEGACY_API_BASE}/readyz`, {
    headers: legacyHeaders(apiKey),
  });
  return parseLegacyResponse(res);
}

export async function legacyModelBenchmark(apiKey?: string): Promise<any> {
  const res = await fetch(`${LEGACY_API_BASE}/model_benchmark`, {
    headers: legacyHeaders(apiKey),
  });
  return parseLegacyResponse(res);
}

export async function legacyOrbitalBrief(apiKey?: string): Promise<any> {
  const res = await fetch(`${LEGACY_API_BASE}/orbital_brief`, {
    headers: legacyHeaders(apiKey),
  });
  return parseLegacyResponse(res);
}
