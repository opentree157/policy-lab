/// <reference types="vite/client" />
const BASE: string = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Dataset {
  id: string;
  name: string;
  slug: string;
  description: string;
  source: string;
  category: string;
  size_bytes: number;
  row_count: number;
  columns: string[];
  tags: string[];
  years_available: number[];
  geographic_level: string;
  created_at: string;
}

export interface Job {
  id: string;
  experiment_id: string;
  worker_id: string | null;
  status: "pending" | "running" | "completed" | "failed";
  logs: string;
  error: string | null;
  peak_cpu_percent: number | null;
  peak_memory_mb: number | null;
  avg_cpu_percent: number | null;
  total_runtime_seconds: number | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface Artifact {
  id: string;
  experiment_id: string;
  name: string;
  artifact_type: string;
  content: unknown;
  size_bytes: number;
  created_at: string;
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  dataset_id: string;
  analysis_type: string;
  parameters: Record<string, unknown>;
  status: "pending" | "running" | "completed" | "failed";
  git_commit: string | null;
  environment_hash: string | null;
  dataset_version: string | null;
  container_image: string | null;
  python_version: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  created_by: string;
  jobs: Job[];
  artifacts: Artifact[];
}

export interface JobMetric {
  elapsed_seconds: number;
  cpu_percent: number;
  memory_mb: number;
  gpu_memory_mb: number;
  gpu_util_percent: number;
  throughput_rows_per_sec: number | null;
}

export interface SystemMetrics {
  cpu_percent: number;
  cpu_count: number;
  memory_used_mb: number;
  memory_total_mb: number;
  memory_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  uptime_seconds: number;
}

export interface ExperimentCreate {
  name: string;
  description: string;
  dataset_id: string;
  analysis_type: string;
  parameters: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const api = {
  datasets: {
    list: () => request<Dataset[]>("/api/v1/datasets/"),
    get: (id: string) => request<Dataset>(`/api/v1/datasets/${id}`),
    templates: () => request<Record<string, unknown>>("/api/v1/datasets/analysis-templates"),
    wbIndicators: () => request<Record<string, { label: string; unit: string; category: string }>>("/api/v1/datasets/wb-indicators"),
  },
  experiments: {
    list: () => request<Experiment[]>("/api/v1/experiments/"),
    get: (id: string) => request<Experiment>(`/api/v1/experiments/${id}`),
    create: (body: ExperimentCreate) =>
      request<Experiment>("/api/v1/experiments/", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    artifacts: (id: string) => request<Artifact[]>(`/api/v1/experiments/${id}/artifacts`),
  },
  jobs: {
    get: (id: string) => request<Job>(`/api/v1/jobs/${id}`),
    metrics: (id: string) => request<JobMetric[]>(`/api/v1/jobs/${id}/metrics`),
    logs: (id: string) => fetch(`${BASE}/api/v1/jobs/${id}/logs`).then((r) => r.text()),
  },
  metrics: {
    system: () => request<SystemMetrics>("/api/v1/metrics/system"),
  },
};
