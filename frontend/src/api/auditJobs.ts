import type { AuditJob } from "../types/audit";

const API_BASE_URL = "http://127.0.0.1:8765";

export interface HealthStatus {
  status: string;
  env: string;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Audit API request failed: ${response.status} ${detail}`);
  }

  return response.json() as Promise<T>;
}

export async function createAuditJob(filePath: string): Promise<AuditJob> {
  return requestJson<AuditJob>("/api/audit-jobs", {
    method: "POST",
    body: JSON.stringify({ file_path: filePath }),
  });
}

export async function getHealthStatus(): Promise<HealthStatus> {
  return requestJson<HealthStatus>("/health");
}
