// 백엔드(FastAPI) 클라이언트 — dev는 vite proxy로 8000 포워딩

export interface Job {
  id: number;
  product_id: number | null;
  style: string;
  status: string;
  video_path: string | null;
  created_at: string;
  approved_by: string | null;
}

export interface Quota {
  date: string;
  used: number;
  limit: number;
  remaining: number;
}

export async function fetchJobs(): Promise<Job[]> {
  const r = await fetch("/jobs");
  if (!r.ok) throw new Error(`jobs ${r.status}`);
  return r.json();
}

export async function fetchQuota(): Promise<Quota> {
  const r = await fetch("/quota");
  if (!r.ok) throw new Error(`quota ${r.status}`);
  return r.json();
}

export async function approve(id: number): Promise<Response> {
  return fetch(`/jobs/${id}/approve`, { method: "POST" });
}

export async function reject(id: number, reason: string): Promise<Response> {
  return fetch(`/jobs/${id}/reject?reason=${encodeURIComponent(reason)}`, {
    method: "POST",
  });
}
