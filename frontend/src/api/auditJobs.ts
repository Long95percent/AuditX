import type { AuditJob, JobTemplate } from "../types/audit";

const API_BASE_URL = "http://127.0.0.1:8765";

export interface HealthStatus {
  status: string;
  env: string;
}

export interface OpenAISettingsPayload {
  api_key?: string | null;
  model: string;
  base_url: string;
}

export interface OpenAISettingsStatus {
  configured: boolean;
  api_key: null;
  model: string;
  base_url: string;
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
    let message = detail;
    try {
      const payload = JSON.parse(detail) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      message = detail;
    }
    throw new Error(`Audit API request failed: ${response.status} ${message}`);
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

export async function saveOpenAISettings(
  payload: OpenAISettingsPayload,
): Promise<OpenAISettingsStatus> {
  return requestJson<OpenAISettingsStatus>("/api/settings/openai", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function testOpenAISettings(): Promise<OpenAISettingsStatus> {
  return requestJson<OpenAISettingsStatus>("/api/settings/openai/test", {
    method: "POST",
  });
}

export async function createJobTemplateFromJD(
  jobName: string,
  jd: string,
): Promise<JobTemplate> {
  return requestJson<JobTemplate>("/api/job-templates/from-jd", {
    method: "POST",
    body: JSON.stringify({ job_name: jobName, jd }),
  });
}
