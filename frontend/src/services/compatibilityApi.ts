import type { BirthInputPayload } from "@/types/birthInput";
import { getApiBase } from "./apiBase";

export type CompatibilityResult = {
  score: 1 | 2 | 3 | 4 | 5;
  score100?: number;
  summary: string;
  attraction: string;
  conflict: string;
  longevity: string;
  reality: {
    emotion: string;
    money: string;
    lifestyle: string;
  };
  guide: string;
};

type PersonPayload = {
  date: string;
  time: string;
  gender: "male" | "female";
  calendarApi: "solar" | "lunar" | "lunar_leap";
};

const COMPATIBILITY_TIMEOUT_MS = 45_000;

export async function postCompatibility(
  birth1: BirthInputPayload,
  birth2: BirthInputPayload
): Promise<CompatibilityResult> {
  const base = getApiBase();
  const url = base ? `${base}/api/compatibility` : "/api/compatibility";
  const p1: PersonPayload = {
    date: birth1.date,
    time: birth1.time,
    gender: birth1.gender,
    calendarApi: birth1.calendarApi,
  };
  const p2: PersonPayload = {
    date: birth2.date,
    time: birth2.time,
    gender: birth2.gender,
    calendarApi: birth2.calendarApi,
  };

  const ctrl = new AbortController();
  const tid = window.setTimeout(() => ctrl.abort(), COMPATIBILITY_TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ birth1: p1, birth2: p2 }),
      signal: ctrl.signal,
    });
  } catch (e) {
    const name = e instanceof Error ? e.name : "";
    if (name === "AbortError" || (e instanceof DOMException && e.name === "AbortError")) {
      throw new Error(
        "요청 시간이 초과되었습니다. 프로젝트 루트에서 API 서버(python scripts/run_api_server_v1.py, 기본 포트 8000)가 실행 중인지 확인해 주세요.",
      );
    }
    if (e instanceof TypeError) {
      throw new Error(
        "서버에 연결할 수 없습니다. 프론트는 npm run dev(5173)·백엔드는 8000에서 실행 중인지 확인해 주세요.",
      );
    }
    throw e;
  } finally {
    window.clearTimeout(tid);
  }

  const raw = await res.text();
  let j: unknown = null;
  try {
    j = raw ? JSON.parse(raw) : null;
  } catch {
    j = null;
  }
  if (!res.ok) {
    const detail =
      typeof j === "object" && j && "detail" in j
        ? String((j as { detail: unknown }).detail)
        : raw || "궁합 분석 중 오류가 발생했습니다.";
    throw new Error(detail);
  }
  if (!j || typeof j !== "object") throw new Error("궁합 응답 형식이 올바르지 않습니다.");
  return j as CompatibilityResult;
}

