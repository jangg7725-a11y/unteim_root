import { getApiBase } from "./apiBase";

export type ApiHealthStatus = "checking" | "ok" | "offline";

/**
 * 백엔드 `/api/health` 확인. base가 비어 있으면 상대 경로(개발 프록시).
 */
export async function fetchApiHealth(signal?: AbortSignal): Promise<boolean> {
  const base = getApiBase();
  const url = base ? `${base}/api/health` : "/api/health";
  try {
    const res = await fetch(url, { method: "GET", signal });
    if (!res.ok) return false;
    const j: unknown = await res.json().catch(() => null);
    return Boolean(j && typeof j === "object" && (j as { ok?: unknown }).ok === true);
  } catch {
    return false;
  }
}
